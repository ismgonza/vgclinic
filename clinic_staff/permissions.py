# clinic_staff/permissions.py
from rest_framework import permissions
from .models import StaffMember

class StaffMemberPermission(permissions.BasePermission):
    """
    Permission for staff members based on their role.
    """
    
    def has_permission(self, request, view):
        # Staff users can access
        if request.user.is_staff:
            return True
            
        # Check if the user has a staff profile in any account
        return StaffMember.objects.filter(
            account_user__user=request.user,
            account_user__is_active=True
        ).exists()
    
    def has_object_permission(self, request, view, obj):
        # Staff users can do anything
        if request.user.is_staff:
            return True
            
        # Check if user is account owner
        if obj.account_user.account.owner == request.user:
            return True
            
        # Staff members can only view/edit themselves or those in same account with proper role
        user_staff = StaffMember.objects.filter(
            account_user__user=request.user,
            account_user__account=obj.account_user.account
        ).first()
        
        if not user_staff:
            return False
            
        # Admins can do anything in their account
        if user_staff.staff_role == StaffMember.ROLE_ADMINISTRATOR:
            return True
            
        # Self-editing is allowed
        if user_staff.pk == obj.pk:
            return request.method in permissions.SAFE_METHODS or request.method == 'PUT'
            
        # Everyone else can only view
        return request.method in permissions.SAFE_METHODS


class InvitationPermission(permissions.BasePermission):
    """
    Permissions for handling invitations.
    """
    
    def has_permission(self, request, view):
        # Accept invitation endpoint is public
        if view.action == 'accept' or request.path.endswith('/accept-invite/'):
            return True
            
        # All other actions require authentication
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        # Staff users can do anything
        if request.user.is_staff:
            return True
            
        # For accepting an invitation, any authenticated user can do it
        if view.action == 'accept' or request.path.endswith('/accept-invite/'):
            return True
            
        # Only admins or owners of the account can manage invitations
        return obj.account.members.filter(
            user=request.user,
            role__in=['admin', 'owner', StaffMember.ROLE_ADMINISTRATOR]
        ).exists()