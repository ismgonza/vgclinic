# clinic_catalog/views.py
from rest_framework import viewsets, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend
from platform_accounts.models import Account, AccountUser
from .models import Specialty, CatalogItem
from .serializers import SpecialtySerializer, CatalogItemSerializer

class SpecialtyViewSet(viewsets.ModelViewSet):
    queryset = Specialty.objects.all()
    serializer_class = SpecialtySerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active']
    search_fields = ['name', 'code', 'description']
    ordering_fields = ['name', 'code']
    
    def get_queryset(self):
        # Get account context
        account = self.get_account_context()
        
        # DEBUG: Print account context
        account_header = self.request.headers.get('X-Account-Context')
        print(f"DEBUG: X-Account-Context header = {account_header}")
        print(f"DEBUG: Resolved account = {account}")
        if account:
            print(f"DEBUG: Account name = {account.account_name}")
        
        # Start with base queryset
        queryset = Specialty.objects.all()
        
        # Filter by account if we have one
        if account:
            queryset = queryset.filter(account=account)
            print(f"DEBUG: Filtered specialties count = {queryset.count()}")
        else:
            print("DEBUG: No account context - showing all specialties user has access to")
            # Fallback: show specialties for accounts the user has access to
            if not self.request.user.is_superuser:
                user_accounts = AccountUser.objects.filter(
                    user=self.request.user,
                    is_active_in_account=True
                ).values_list('account', flat=True)
                queryset = queryset.filter(account__in=user_accounts)
        
        return queryset
    
    def get_account_context(self):
        """Get and validate account context from request header"""
        account_id = self.request.headers.get('X-Account-Context')
        
        if not account_id:
            return None
            
        try:
            account = Account.objects.get(account_id=account_id)
            
            # Check if user has access (unless they're staff/superuser)
            if self.request.user.is_staff or self.request.user.is_superuser:
                return account
            else:
                # Check if user is a member of this account
                if AccountUser.objects.filter(
                    user=self.request.user,
                    account=account,
                    is_active_in_account=True
                ).exists():
                    return account
                    
            return None
        except Account.DoesNotExist:
            return None

class CatalogItemViewSet(viewsets.ModelViewSet):
    queryset = CatalogItem.objects.all()
    serializer_class = CatalogItemSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['specialty', 'is_active', 'is_variable_price']
    search_fields = ['name', 'code', 'description']
    ordering_fields = ['name', 'code', 'price']
    
    def get_queryset(self):
        # Get account context
        account = self.get_account_context()
        
        # DEBUG: Print account context
        account_header = self.request.headers.get('X-Account-Context')
        print(f"DEBUG: X-Account-Context header = {account_header}")
        print(f"DEBUG: Resolved account = {account}")
        if account:
            print(f"DEBUG: Account name = {account.account_name}")
        
        # Start with base queryset
        queryset = CatalogItem.objects.all()
        
        # Filter by account if we have one
        if account:
            # Filter catalog items by account
            queryset = queryset.filter(account=account)
            print(f"DEBUG: Filtered catalog items count = {queryset.count()}")
        else:
            print("DEBUG: No account context - showing all catalog items user has access to")
            # Fallback: show items for accounts the user has access to
            if not self.request.user.is_superuser:
                user_accounts = AccountUser.objects.filter(
                    user=self.request.user,
                    is_active_in_account=True
                ).values_list('account', flat=True)
                queryset = queryset.filter(account__in=user_accounts)
        
        return queryset
    
    def get_account_context(self):
        """Get and validate account context from request header"""
        account_id = self.request.headers.get('X-Account-Context')
        
        if not account_id:
            return None
            
        try:
            account = Account.objects.get(account_id=account_id)
            
            # Check if user has access (unless they're staff/superuser)
            if self.request.user.is_staff or self.request.user.is_superuser:
                return account
            else:
                # Check if user is a member of this account
                if AccountUser.objects.filter(
                    user=self.request.user,
                    account=account,
                    is_active_in_account=True
                ).exists():
                    return account
                    
            return None
        except Account.DoesNotExist:
            return None