# clinic_catalog/views.py - UPDATED with permission checks
from rest_framework import viewsets, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend
from platform_accounts.models import Account, AccountUser
from core.permissions import AccountPermissionMixin
from .models import Specialty, CatalogItem
from .serializers import SpecialtySerializer, CatalogItemSerializer

class SpecialtyViewSet(AccountPermissionMixin, viewsets.ModelViewSet):
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
        
        if not account:
            # No account context - show specialties from all user's accounts
            if self.request.user.is_superuser:
                return Specialty.objects.all()
            else:
                print("DEBUG: No account context - showing all specialties user has access to")
                user_accounts = AccountUser.objects.filter(
                    user=self.request.user,
                    is_active_in_account=True
                ).values_list('account', flat=True)
                return Specialty.objects.filter(account__in=user_accounts)
        
        # Check if user has permission to view specialties
        if not self.check_permission('view_specialties_list', account):
            return Specialty.objects.none()
        
        # Filter by account if we have one
        queryset = Specialty.objects.filter(account=account)
        print(f"DEBUG: Filtered specialties count = {queryset.count()}")
        return queryset
    
    def create(self, request, *args, **kwargs):
        """Override create to check manage_specialties permission."""
        account = self.get_account_context()
        
        permission_error = self.require_permission('manage_specialties', account)
        if permission_error:
            return permission_error
            
        return super().create(request, *args, **kwargs)
    
    def update(self, request, *args, **kwargs):
        """Override update to check manage_specialties permission."""
        account = self.get_account_context()
        
        permission_error = self.require_permission('manage_specialties', account)
        if permission_error:
            return permission_error
            
        return super().update(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        """Override destroy to check manage_specialties permission."""
        account = self.get_account_context()
        
        permission_error = self.require_permission('manage_specialties', account)
        if permission_error:
            return permission_error
            
        return super().destroy(request, *args, **kwargs)

class CatalogItemViewSet(AccountPermissionMixin, viewsets.ModelViewSet):
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
        
        if not account:
            # No account context - show catalog items from all user's accounts
            if self.request.user.is_superuser:
                return CatalogItem.objects.all()
            else:
                print("DEBUG: No account context - showing all catalog items user has access to")
                user_accounts = AccountUser.objects.filter(
                    user=self.request.user,
                    is_active_in_account=True
                ).values_list('account', flat=True)
                return CatalogItem.objects.filter(account__in=user_accounts)
        
        # Check if user has permission to view procedures (catalog items)
        if not self.check_permission('view_procedures_list', account):
            return CatalogItem.objects.none()
        
        # Filter catalog items by account
        queryset = CatalogItem.objects.filter(account=account)
        print(f"DEBUG: Filtered catalog items count = {queryset.count()}")
        return queryset
    
    def create(self, request, *args, **kwargs):
        """Override create to check manage_procedures permission."""
        account = self.get_account_context()
        
        permission_error = self.require_permission('manage_procedures', account)
        if permission_error:
            return permission_error
            
        return super().create(request, *args, **kwargs)
    
    def update(self, request, *args, **kwargs):
        """Override update to check manage_procedures permission."""
        account = self.get_account_context()
        
        permission_error = self.require_permission('manage_procedures', account)
        if permission_error:
            return permission_error
            
        return super().update(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        """Override destroy to check manage_procedures permission."""
        account = self.get_account_context()
        
        permission_error = self.require_permission('manage_procedures', account)
        if permission_error:
            return permission_error
            
        return super().destroy(request, *args, **kwargs)