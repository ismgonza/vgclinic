# platform_accounts/views.py
from rest_framework import viewsets, permissions
from .models import Account, Role, AccountUser
from .serializers import AccountSerializer, RoleSerializer, AccountUserSerializer

class IsAccountMemberOrAdmin(permissions.BasePermission):
    """
    Custom permission to only allow members of an account to access it.
    """
    def has_object_permission(self, request, view, obj):
        # Check if the user is a member of the account or is a superuser
        if request.user.is_superuser:
            return True
        
        # For Account objects
        if isinstance(obj, Account):
            return AccountUser.objects.filter(user=request.user, account=obj).exists()
        
        # For AccountUser objects
        if isinstance(obj, AccountUser):
            return obj.user == request.user or AccountUser.objects.filter(
                user=request.user, account=obj.account, role__id__in=['own', 'adm']
            ).exists()
        
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
        # Otherwise, return only accounts the user is a member of
        if self.request.user.is_superuser:
            return Account.objects.all()
        
        # Get accounts where the user is a member
        user_accounts = AccountUser.objects.filter(user=self.request.user).values_list('account', flat=True)
        return Account.objects.filter(account_id__in=user_accounts)

class RoleViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows roles to be viewed.
    """
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    permission_classes = [permissions.IsAuthenticated]

class AccountUserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows account users to be viewed or edited.
    """
    queryset = AccountUser.objects.all()
    serializer_class = AccountUserSerializer
    permission_classes = [permissions.IsAuthenticated, IsAccountMemberOrAdmin]
    
    def get_queryset(self):
        # If user is superuser, return all account users
        # Otherwise, filter based on user's accounts and permissions
        if self.request.user.is_superuser:
            return AccountUser.objects.all()
        
        # Get accounts where the user is an admin or owner
        admin_accounts = AccountUser.objects.filter(
            user=self.request.user, 
            role__id__in=['own', 'adm']
        ).values_list('account', flat=True)
        
        # Return the user's own account user records and all account users of accounts where they're admin
        return AccountUser.objects.filter(
            models.Q(user=self.request.user) | models.Q(account__account_id__in=admin_accounts)
        )