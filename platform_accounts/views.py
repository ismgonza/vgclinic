# platform_accounts/views.py
from rest_framework import viewsets, permissions
from django.db import models
from .models import Account, AccountOwner, AccountUser
from .serializers import AccountSerializer, AccountOwnerSerializer, AccountUserSerializer

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

class AccountUserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows account users to be viewed or edited.
    """
    queryset = AccountUser.objects.all()
    serializer_class = AccountUserSerializer
    permission_classes = [permissions.IsAuthenticated, IsAccountMemberOrAdmin]
    
    def get_queryset(self):
        # If user is superuser, return all account users
        if self.request.user.is_superuser:
            return AccountUser.objects.all()
        
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
        )