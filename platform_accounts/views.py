# platform_accounts/views.py - FIXED VERSION
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import viewsets, permissions, status
from django.db import models, transaction
from core.permissions import AccountPermissionMixin
from .models import Account, AccountOwner, AccountUser, AccountInvitation, AccountAuthorization
from .serializers import (AccountSerializer, AccountOwnerSerializer, AccountUserSerializer, 
                          AccountInvitationSerializer, CreateInvitationSerializer, 
                          AcceptInvitationSerializer, AccountAuthorizationSerializer,
                          UserPermissionsSerializer)
import logging

logger = logging.getLogger(__name__)


class IsAccountMemberOrAdmin(permissions.BasePermission):
    """
    Custom permission to only allow members of an account to access it.
    Owners automatically have all permissions.
    """
    def has_object_permission(self, request, view, obj):
        # Check if the user is a superuser
        if request.user.is_superuser:
            return True
        
        # For Account objects
        if isinstance(obj, Account):
            # Check if user is owner of this account
            if AccountOwner.objects.filter(user=request.user, account=obj, is_active=True).exists():
                return True
            # Check if user is a member of this account
            return AccountUser.objects.filter(user=request.user, account=obj, is_active_in_account=True).exists()
        
        # For AccountUser objects
        if isinstance(obj, AccountUser):
            # User can access their own record
            if obj.user == request.user:
                return True
            # Check if user is owner of the account
            if AccountOwner.objects.filter(user=request.user, account=obj.account, is_active=True).exists():
                return True
            # Check if user is admin of the account
            return AccountUser.objects.filter(
                user=request.user, 
                account=obj.account, 
                role='adm',
                is_active_in_account=True
            ).exists()
        
        # For AccountOwner objects
        if isinstance(obj, AccountOwner):
            # User can access their own ownership record
            if obj.user == request.user:
                return True
            # Check if user is owner of the account (owners can manage other owners)
            return AccountOwner.objects.filter(user=request.user, account=obj.account, is_active=True).exists()
        
        return False

class AccountViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows accounts to be viewed or edited.
    """
    queryset = Account.objects.all()
    serializer_class = AccountSerializer
    permission_classes = [permissions.IsAuthenticated, IsAccountMemberOrAdmin]
    
    def get_queryset(self):
        # If user is superuser, return all accounts
        if self.request.user.is_superuser:
            return Account.objects.all()
        
        # Get accounts where the user is an owner
        owned_accounts = AccountOwner.objects.filter(
            user=self.request.user, 
            is_active=True
        ).values_list('account', flat=True)
        
        # Get accounts where the user is a member
        member_accounts = AccountUser.objects.filter(
            user=self.request.user,
            is_active_in_account=True
        ).values_list('account', flat=True)
        
        # Combine both querysets
        all_account_ids = list(owned_accounts) + list(member_accounts)
        return Account.objects.filter(account_id__in=all_account_ids)

class AccountOwnerViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows account ownership to be viewed or edited.
    """
    queryset = AccountOwner.objects.all()
    serializer_class = AccountOwnerSerializer
    permission_classes = [permissions.IsAuthenticated, IsAccountMemberOrAdmin]
    
    def get_queryset(self):
        # If user is superuser, return all ownership records
        if self.request.user.is_superuser:
            return AccountOwner.objects.all()
        
        # Get accounts where the user is an owner (owners can see other owners)
        owned_accounts = AccountOwner.objects.filter(
            user=self.request.user, 
            is_active=True
        ).values_list('account', flat=True)
        
        # Return ownership records for accounts they own, plus their own records
        return AccountOwner.objects.filter(
            models.Q(user=self.request.user) | 
            models.Q(account__account_id__in=owned_accounts)
        )

class AccountUserViewSet(AccountPermissionMixin, viewsets.ModelViewSet):
    """
    API endpoint that allows account users to be viewed or edited.
    """
    queryset = AccountUser.objects.all()
    serializer_class = AccountUserSerializer
    permission_classes = [permissions.IsAuthenticated, IsAccountMemberOrAdmin]
    
    def get_queryset(self):
        # Get account context from headers first
        account = self.get_account_context()
        
        if account:
            # Check if user has permission to view team members
            if not self.check_permission('view_team_members_list', account):
                return AccountUser.objects.none()
            
            # Filter by the specific account from headers
            return AccountUser.objects.filter(account=account).select_related('user', 'specialty')
        
        # Fallback to original logic if no account context
        if self.request.user.is_superuser:
            return AccountUser.objects.all().select_related('user', 'specialty')
        
        # Get accounts where the user is an owner
        owned_accounts = AccountOwner.objects.filter(
            user=self.request.user, 
            is_active=True
        ).values_list('account', flat=True)
        
        # Get accounts where the user is an admin
        admin_accounts = AccountUser.objects.filter(
            user=self.request.user, 
            role='adm',
            is_active_in_account=True
        ).values_list('account', flat=True)
        
        # Combine owned and admin accounts
        manageable_accounts = list(owned_accounts) + list(admin_accounts)
        
        # Return the user's own account user records and all account users of accounts they can manage
        return AccountUser.objects.filter(
            models.Q(user=self.request.user) | 
            models.Q(account__account_id__in=manageable_accounts)
        ).select_related('user', 'specialty')
    
    def create(self, request, *args, **kwargs):
        """Override create to check manage_team_members permission."""
        account = self.get_account_context()
        
        permission_error = self.require_permission('manage_team_members', account)
        if permission_error:
            return permission_error
            
        return super().create(request, *args, **kwargs)
    
    def update(self, request, *args, **kwargs):
        """Override update to check manage_team_members permission."""
        account = self.get_account_context()
        
        permission_error = self.require_permission('manage_team_members', account)
        if permission_error:
            return permission_error
            
        return super().update(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        """Override destroy to check manage_team_members permission."""
        account = self.get_account_context()
        
        permission_error = self.require_permission('manage_team_members', account)
        if permission_error:
            return permission_error
            
        return super().destroy(request, *args, **kwargs)
        
    @action(detail=True, methods=['patch'])
    def deactivate(self, request, pk=None):
        """Deactivate a team member."""
        account = self.get_account_context()
        
        permission_error = self.require_permission('manage_team_members', account)
        if permission_error:
            return permission_error
        
        account_user = self.get_object()
        account_user.is_active_in_account = False
        account_user.save()
        
        return Response({'message': 'Team member deactivated successfully'})

    @action(detail=True, methods=['patch'])
    def reactivate(self, request, pk=None):
        """Reactivate a team member."""
        account = self.get_account_context()
        
        permission_error = self.require_permission('manage_team_members', account)
        if permission_error:
            return permission_error
        
        account_user = self.get_object()
        account_user.is_active_in_account = True
        account_user.save()
        
        return Response({'message': 'Team member reactivated successfully'})

class AccountInvitationViewSet(AccountPermissionMixin, viewsets.ModelViewSet):
    """
    API endpoint for managing account invitations.
    """
    queryset = AccountInvitation.objects.all()
    serializer_class = AccountInvitationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Filter invitations based on user permissions and account context."""
        # Get account context from headers first
        account = self.get_account_context()
        
        if account:
            # Check if user has permission to view invitations
            if not self.check_permission('view_invitations_list', account):
                return AccountInvitation.objects.none()
            
            # Filter by the specific account from headers
            return AccountInvitation.objects.filter(account=account).select_related('account', 'specialty', 'invited_by')
        
        # Fallback to original logic if no account context
        if self.request.user.is_superuser:
            return AccountInvitation.objects.all().select_related('account', 'specialty', 'invited_by')
        
        # Get accounts where user can invite users
        accessible_accounts = []
        
        # Add owned accounts
        owned_accounts = AccountOwner.objects.filter(
            user=self.request.user, 
            is_active=True
        ).values_list('account', flat=True)
        accessible_accounts.extend(owned_accounts)
        
        # Add accounts where user has manage_invitations authorization
        for account_user in AccountUser.objects.filter(user=self.request.user, is_active_in_account=True):
            if account_user.has_permission('manage_invitations'):
                accessible_accounts.append(account_user.account.account_id)
        
        return AccountInvitation.objects.filter(
            account__account_id__in=accessible_accounts
        ).select_related('account', 'specialty', 'invited_by')
    
    def get_serializer_class(self):
        """Use different serializer for creation."""
        if self.action == 'create':
            return CreateInvitationSerializer
        return AccountInvitationSerializer
    
    def perform_create(self, serializer):
        """Set the invited_by field when creating invitations."""
        # Check if user has permission to invite to this account
        account = serializer.validated_data['account']
        
        # Check permission before proceeding
        if not self.check_permission('manage_invitations', account):
            raise permissions.PermissionDenied("You don't have permission to invite users to this account.")
        
        # Check if user is owner or has manage_invitations authorization (legacy check)
        is_owner = AccountOwner.objects.filter(
            user=self.request.user, 
            account=account, 
            is_active=True
        ).exists()
        
        has_permission = AccountUser.user_has_permission(
            self.request.user, 
            account, 
            'manage_invitations'
        )
        
        if not (is_owner or has_permission):
            raise permissions.PermissionDenied("You don't have permission to invite users to this account.")
        
        # Save the invitation
        invitation = serializer.save(invited_by=self.request.user)
        
        # Send invitation email
        try:
            from .services import InvitationEmailService
            email_sent = InvitationEmailService.send_invitation_email(invitation)
            
            if not email_sent:
                logger.warning(f"Failed to send invitation email for invitation {invitation.id}")
        except ImportError:
            logger.warning("InvitationEmailService not available - email not sent")
    
    def update(self, request, *args, **kwargs):
        """Override update to check manage_invitations permission."""
        account = self.get_account_context()
        
        permission_error = self.require_permission('manage_invitations', account)
        if permission_error:
            return permission_error
            
        return super().update(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        """Override destroy to check manage_invitations permission."""
        account = self.get_account_context()
        
        permission_error = self.require_permission('manage_invitations', account)
        if permission_error:
            return permission_error
            
        return super().destroy(request, *args, **kwargs)
    
    @action(detail=True, methods=['post'])
    def resend(self, request, pk=None):
        """Resend an invitation email."""
        account = self.get_account_context()
        
        permission_error = self.require_permission('manage_invitations', account)
        if permission_error:
            return permission_error
        
        invitation = self.get_object()
        
        if invitation.status != 'pending':
            return Response(
                {'error': 'Can only resend pending invitations'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if invitation.is_expired():
            return Response(
                {'error': 'Cannot resend expired invitation'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Send invitation email
        try:
            from .services import InvitationEmailService
            email_sent = InvitationEmailService.send_invitation_email(invitation)
            
            if email_sent:
                return Response({'message': 'Invitation resent successfully'})
            else:
                return Response(
                    {'error': 'Failed to send invitation email'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        except ImportError:
            return Response({'message': 'Invitation marked for resend (email service unavailable)'})
    
    @action(detail=True, methods=['patch'])
    def revoke(self, request, pk=None):
        """Revoke an invitation."""
        account = self.get_account_context()
        
        permission_error = self.require_permission('manage_invitations', account)
        if permission_error:
            return permission_error
        
        invitation = self.get_object()
        
        if invitation.status != 'pending':
            return Response(
                {'error': 'Can only revoke pending invitations'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        invitation.mark_as_revoked()
        
        return Response({'message': 'Invitation revoked successfully'})

class InvitationAcceptanceView(viewsets.GenericViewSet):
    """
    API endpoint for accepting invitations.
    This is separate from the main viewset because it doesn't require authentication.
    """
    permission_classes = [permissions.AllowAny]  # No auth required for acceptance
    serializer_class = AcceptInvitationSerializer  # Add default serializer
    
    @action(detail=False, methods=['get'], url_path='(?P<token>[^/.]+)')
    def validate_token(self, request, token=None):
        """Validate an invitation token and return invitation details."""
        try:
            invitation = AccountInvitation.objects.get(token=token)
            
            if not invitation.is_valid():
                if invitation.is_expired():
                    return Response(
                        {'error': 'This invitation has expired', 'expired': True},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                else:
                    return Response(
                        {'error': 'This invitation is no longer valid', 'invalid': True},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            # Check if user already exists
            from platform_users.models import User
            user_exists = User.objects.filter(email=invitation.email).exists()
            
            return Response({
                'valid': True,
                'email': invitation.email,
                'account_name': invitation.account.account_name,
                'role': invitation.get_role_display(),
                'specialty': invitation.specialty.name if invitation.specialty else None,
                'personal_message': invitation.personal_message,
                'user_exists': user_exists,
                'expires_at': invitation.expires_at
            })
            
        except AccountInvitation.DoesNotExist:
            return Response(
                {'error': 'Invalid invitation token'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=False, methods=['post'])
    def accept(self, request, **kwargs):
        """Accept an invitation."""
        serializer = AcceptInvitationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        invitation = serializer.validated_data['invitation']
        
        with transaction.atomic():
            # Check if user exists or create new user
            if 'existing_user' in serializer.validated_data:
                user = serializer.validated_data['existing_user']
            else:
                # Create new user
                from platform_users.models import User
                user = User.objects.create_user(
                    email=invitation.email,
                    first_name=serializer.validated_data['first_name'],
                    last_name=serializer.validated_data['last_name'],
                    id_type=serializer.validated_data['id_type'],
                    id_number=serializer.validated_data['id_number'],
                    password=serializer.validated_data['password']
                )
            
            # Create AccountUser relationship
            account_user = AccountUser.objects.create(
                user=user,
                account=invitation.account,
                role=invitation.role,
                specialty=invitation.specialty,
                is_active_in_account=True
            )
            
            # Mark invitation as accepted
            invitation.mark_as_accepted(user)
            
            # Send welcome email
            try:
                from .services import InvitationEmailService
                InvitationEmailService.send_welcome_email(user, invitation.account)
            except ImportError:
                logger.warning("InvitationEmailService not available - welcome email not sent")
        
        return Response({
            'message': 'Invitation accepted successfully',
            'user_id': user.id,
            'account_id': str(invitation.account.account_id),
            'role': invitation.role
        }, status=status.HTTP_201_CREATED)

class AccountPermissionViewSet(AccountPermissionMixin, viewsets.GenericViewSet):
    """
    API endpoint for managing user permissions within accounts.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def check_permission_management_access(self, account):
        """Check if user can manage permissions for this account."""
        if self.request.user.is_staff or self.request.user.is_superuser:
            return True
            
        # Check if user is owner
        if AccountOwner.objects.filter(
            user=self.request.user,
            account=account,
            is_active=True
        ).exists():
            return True
        
        # Use the permission method to check manage_permissions
        return self.check_permission('manage_permissions', account)
    
    @action(detail=False, methods=['get'])
    def available_permissions(self, request):
        """Get list of all available permissions."""
        # No specific permission check needed - this is just metadata
        from .permissions import get_all_permissions, PERMISSION_CATEGORIES
        
        permissions = [
            {
                'key': key,
                'display': str(display),
                'category': self.get_permission_category(key)
            }
            for key, display in get_all_permissions()
        ]
        
        # Use the centralized categories
        categories = {}
        for category_key, category_name in PERMISSION_CATEGORIES.items():
            categories[category_key] = str(category_name)
        
        return Response({
            'permissions': permissions,
            'categories': categories
        })
    
    def get_permission_category(self, permission_key):
        """Categorize permissions for better UI organization."""
        if permission_key.startswith(('view_patients', 'manage_patients')):
            return 'patient_management'
        elif permission_key.startswith(('view_treatment', 'create_treatment', 'edit_treatment')):
            return 'treatment_management'
        elif permission_key.startswith(('view_locations', 'manage_locations', 'view_rooms', 'manage_rooms', 'view_specialties', 'manage_specialties', 'view_procedures', 'manage_procedures')):
            return 'catalog_management'
        elif permission_key.startswith(('view_team', 'manage_team', 'view_invitations', 'manage_invitations', 'view_permissions', 'manage_permissions')):
            return 'team_management'
        elif permission_key.startswith(('view_appointments', 'manage_appointments', 'manage_schedule')):
            return 'appointment_management'
        elif permission_key.startswith(('view_billing', 'manage_billing', 'view_financial', 'manage_pricing')):
            return 'billing_management'
        elif permission_key.startswith(('view_reports', 'view_analytics', 'export_reports')):
            return 'reporting_analytics'
        else:
            return 'other'
    
    @action(detail=False, methods=['get'])
    def users_permissions(self, request):
        """Get permissions summary for all users in the account."""
        account = self.get_account_context()
        if not account:
            return Response(
                {'error': 'Account context required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if user has permission to view permissions
        if not self.check_permission('view_permissions_list', account):
            return Response(
                {'error': 'Permission denied. You need "view_permissions_list" permission to view user permissions.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get all users in this account
        account_users = AccountUser.objects.filter(
            account=account,
            is_active_in_account=True
        ).select_related('user', 'specialty')
        
        users_data = []
        for account_user in account_users:
            # Check if user is owner
            is_owner = AccountOwner.objects.filter(
                user=account_user.user,
                account=account,
                is_active=True
            ).exists()
            
            # Get user's explicit permissions
            user_permissions = AccountAuthorization.objects.filter(
                user=account_user.user,
                account=account,
                is_active=True
            )
            
            # Get permission keys
            permission_keys = []
            role_permissions = []
            individual_permissions = []
            
            if is_owner:
                from .permissions import get_all_permissions
                permission_keys = [key for key, _ in get_all_permissions()]
                role_permissions = permission_keys  # Owners have all as "role"
            else:
                # Get role-based permissions (Custom roles have no defaults)
                if account_user.role != 'cus':
                    from .models import RolePermission
                    role_perms = RolePermission.objects.filter(
                        role=account_user.role,
                        is_active=True
                    ).values_list('permission_type', flat=True)
                    role_permissions = list(role_perms)
                
                # Get individual permissions (explicitly granted)
                individual_perms = [
                    auth.authorization_type 
                    for auth in user_permissions 
                    if auth.is_valid()
                ]
                individual_permissions = individual_perms
                
                # Combine both
                permission_keys = list(set(role_permissions + individual_permissions))

            users_data.append({
                'user_id': account_user.user.id,
                'user_details': {
                    'id': account_user.user.id,
                    'email': account_user.user.email,
                    'first_name': account_user.user.first_name,
                    'last_name': account_user.user.last_name,
                    'full_name': account_user.user.get_full_name(),
                },
                'role': account_user.role,
                'role_display': account_user.get_role_display(),
                'is_owner': is_owner,
                'permissions': permission_keys,
                'role_permissions': role_permissions,
                'individual_permissions': individual_permissions,
                'permission_details': AccountAuthorizationSerializer(user_permissions, many=True).data
            })
        
        return Response({'users': users_data})
    
    @action(detail=False, methods=['post'])
    def update_user_permissions(self, request):
        """Update permissions for a specific user."""
        account = self.get_account_context()
        if not account:
            return Response(
                {'error': 'Account context required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not self.check_permission_management_access(account):
            return Response(
                {'error': 'Permission denied. You need "manage_permissions" permission to update user permissions.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = UserPermissionsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user_id = serializer.validated_data['user_id']
        permissions = serializer.validated_data['permissions']
        notes = serializer.validated_data.get('notes', '')
        
        # Verify user is in this account
        try:
            from platform_users.models import User
            user = User.objects.get(id=user_id)
            account_user = AccountUser.objects.get(
                user=user,
                account=account,
                is_active_in_account=True
            )
        except (User.DoesNotExist, AccountUser.DoesNotExist):
            return Response(
                {'error': 'User not found in this account'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check if user is owner (can't modify owner permissions this way)
        is_owner = AccountOwner.objects.filter(
            user=user,
            account=account,
            is_active=True
        ).exists()
        
        if is_owner:
            return Response(
                {'error': 'Cannot modify permissions for account owners'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        with transaction.atomic():
            # Remove existing permissions
            AccountAuthorization.objects.filter(
                user=user,
                account=account
            ).delete()
            
            # Add new permissions
            for permission_type in permissions:
                AccountAuthorization.objects.create(
                    user=user,
                    account=account,
                    authorization_type=permission_type,
                    granted_by=request.user,
                    is_active=True,
                    notes=notes
                )
        
        return Response({
            'message': f'Successfully updated permissions for {user.get_full_name()}',
            'permissions_granted': permissions
        })
    
    @action(detail=False, methods=['get'], url_path='user/(?P<user_id>[^/.]+)')
    def user_permissions(self, request, user_id=None):
        """Get detailed permissions for a specific user."""
        account = self.get_account_context()
        if not account:
            return Response(
                {'error': 'Account context required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if user is viewing their own permissions OR has permission to view others
        if str(user_id) != str(request.user.id):
            if not self.check_permission('view_permissions_detail', account):
                return Response(
                    {'error': 'Permission denied. You need "view_permissions_detail" permission to view other users\' permissions.'},
                    status=status.HTTP_403_FORBIDDEN
                )
        
        try:
            from platform_users.models import User
            user = User.objects.get(id=user_id)
            account_user = AccountUser.objects.get(
                user=user,
                account=account,
                is_active_in_account=True
            )
        except (User.DoesNotExist, AccountUser.DoesNotExist):
            return Response(
                {'error': 'User not found in this account'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check if user is owner
        is_owner = AccountOwner.objects.filter(
            user=user,
            account=account,
            is_active=True
        ).exists()
        
        # Get user's explicit permissions
        user_permissions = AccountAuthorization.objects.filter(
            user=user,
            account=account,
            is_active=True
        )
        
        # Get permission breakdown
        permission_keys = []
        role_permissions = []
        individual_permissions = []
        
        if is_owner:
            from .permissions import get_all_permissions
            permission_keys = [key for key, _ in get_all_permissions()]
            role_permissions = permission_keys  # Owners have all as "role"
        else:
            # Get role-based permissions (Custom roles have no defaults)
            if account_user.role != 'cus':
                from .models import RolePermission
                role_perms = RolePermission.objects.filter(
                    role=account_user.role,
                    is_active=True
                ).values_list('permission_type', flat=True)
                role_permissions = list(role_perms)
            
            # Get individual permissions (explicitly granted)
            individual_perms = [
                auth.authorization_type 
                for auth in user_permissions 
                if auth.is_valid()
            ]
            individual_permissions = individual_perms
            
            # Combine both
            permission_keys = list(set(role_permissions + individual_permissions))
        
        return Response({
            'user_id': user.id,
            'user_details': {
                'id': user.id,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'full_name': user.get_full_name(),
            },
            'role': account_user.role,
            'role_display': account_user.get_role_display(),
            'is_owner': is_owner,
            'permissions': permission_keys,
            'role_permissions': role_permissions,
            'individual_permissions': individual_permissions,
            'permission_details': AccountAuthorizationSerializer(user_permissions, many=True).data
        })
        
    @action(detail=False, methods=['get'], url_path='my-permissions')
    def my_permissions(self, request):
        """Get current user's own permissions - no special permissions required."""
        account = self.get_account_context()
        if not account:
            return Response(
                {'error': 'Account context required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user = request.user
        
        try:
            account_user = AccountUser.objects.get(
                user=user,
                account=account,
                is_active_in_account=True
            )
        except AccountUser.DoesNotExist:
            return Response(
                {'error': 'User not found in this account'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check if user is owner
        is_owner = AccountOwner.objects.filter(
            user=user,
            account=account,
            is_active=True
        ).exists()
        
        # Get user's explicit permissions
        user_permissions = AccountAuthorization.objects.filter(
            user=user,
            account=account,
            is_active=True
        )
        
        # Get permission breakdown
        permission_keys = []
        role_permissions = []
        individual_permissions = []
        
        if is_owner:
            from .permissions import get_all_permissions
            permission_keys = [key for key, _ in get_all_permissions()]
            role_permissions = permission_keys  # Owners have all as "role"
        else:
            # Get role-based permissions (Custom roles have no defaults)
            if account_user.role != 'cus':
                from .permissions import get_default_permissions_for_role
                role_permissions = get_default_permissions_for_role(account_user.role)
            
            # Get individual permissions (explicitly granted)
            individual_perms = [
                auth.authorization_type 
                for auth in user_permissions 
                if auth.is_valid()
            ]
            individual_permissions = individual_perms
            
            # Combine both
            permission_keys = list(set(role_permissions + individual_permissions))
        
        return Response({
            'user_id': user.id,
            'role': account_user.role,
            'role_display': account_user.get_role_display(),
            'is_owner': is_owner,
            'permissions': permission_keys,
            'role_permissions': role_permissions,
            'individual_permissions': individual_permissions,
        })