# platform_accounts/permissions.py
from rest_framework import permissions

class IsAccountOwnerOrAdmin(permissions.BasePermission):
    """
    Custom permission to only allow owners or admins of an account to modify it.
    """
    
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request
        if request.method in permissions.SAFE_METHODS:
            return True
            
        # Check if user is staff
        if request.user.is_staff:
            return True
            
        # Check if user is owner or admin of the account
        if hasattr(obj, 'account'):
            account = obj.account
        else:
            account = obj
            
        # Check if user is owner
        if account.owner == request.user:
            return True
            
        # Check if user is admin in this account
        return account.members.filter(
            user=request.user,
            role__in=['admin', 'owner']
        ).exists()


class IsAccountMember(permissions.BasePermission):
    """
    Custom permission to only allow members of an account to view its details.
    """
    
    def has_object_permission(self, request, view, obj):
        # Staff can do anything
        if request.user.is_staff:
            return True
            
        # Get the account from the object
        if hasattr(obj, 'account'):
            account = obj.account
        elif hasattr(obj, 'account_user') and hasattr(obj.account_user, 'account'):
            # Handle StaffMember objects which have account_user.account
            account = obj.account_user.account
        elif hasattr(obj, 'location') and hasattr(obj.location, 'account'):
            # Handle Room objects which have location.account
            account = obj.location.account
        else:
            account = obj
            
        # Check if user is a member of this account
        return account.members.filter(user=request.user).exists()