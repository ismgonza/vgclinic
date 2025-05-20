# clinic_catalog/views.py
from rest_framework import viewsets, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend
from platform_accounts.models import AccountUser
from .models import Specialty, CatalogItem
from .serializers import SpecialtySerializer, CatalogItemSerializer

# Custom permission to check if user has access to the account
class HasAccountAccess(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        # Check if user is superuser
        if request.user.is_superuser:
            return True
        
        # Get account from object
        account = getattr(obj, 'account', None)
        if not account:
            return False
            
        # Check if user has access to the account
        return AccountUser.objects.filter(
            user=request.user,
            account=account,
            is_active_in_account=True
        ).exists()

class SpecialtyViewSet(viewsets.ModelViewSet):
    queryset = Specialty.objects.all()
    serializer_class = SpecialtySerializer
    permission_classes = [permissions.IsAuthenticated, HasAccountAccess]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['account', 'is_active']
    search_fields = ['name', 'code', 'description']
    ordering_fields = ['name', 'code']
    
    def get_queryset(self):
        # If superuser, return all
        if self.request.user.is_superuser:
            return Specialty.objects.all()
            
        # Otherwise, return specialties for accounts the user has access to
        user_accounts = AccountUser.objects.filter(
            user=self.request.user,
            is_active_in_account=True
        ).values_list('account', flat=True)
        
        return Specialty.objects.filter(account__in=user_accounts)

class CatalogItemViewSet(viewsets.ModelViewSet):
    queryset = CatalogItem.objects.all()
    serializer_class = CatalogItemSerializer
    permission_classes = [permissions.IsAuthenticated, HasAccountAccess]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['account', 'specialty', 'is_active', 'is_variable_price']
    search_fields = ['name', 'code', 'description']
    ordering_fields = ['name', 'code', 'price']
    
    def get_queryset(self):
        # If superuser, return all
        if self.request.user.is_superuser:
            return CatalogItem.objects.all()
            
        # Otherwise, return items for accounts the user has access to
        user_accounts = AccountUser.objects.filter(
            user=self.request.user,
            is_active_in_account=True
        ).values_list('account', flat=True)
        
        return CatalogItem.objects.filter(account__in=user_accounts)