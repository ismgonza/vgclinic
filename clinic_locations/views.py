# clinic_locations/views.py - UPDATED with permission checks
from rest_framework import viewsets, permissions, filters, status
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from platform_accounts.models import Account, AccountUser
from core.permissions import AccountPermissionMixin
from .models import Branch, Room
from .serializers import BranchSerializer, RoomSerializer

class BranchViewSet(AccountPermissionMixin, viewsets.ModelViewSet):
    queryset = Branch.objects.all()
    serializer_class = BranchSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active', 'province']
    search_fields = ['name', 'email', 'phone', 'address']
    ordering_fields = ['name', 'province']
    
    def get_queryset(self):
        # Get account context
        account = self.get_account_context()
        
        if not account:
            # No account context - show branches from all user's accounts
            if self.request.user.is_superuser:
                return Branch.objects.all()
            else:
                user_accounts = AccountUser.objects.filter(
                    user=self.request.user,
                    is_active_in_account=True
                ).values_list('account', flat=True)
                return Branch.objects.filter(account__in=user_accounts)
        
        # Check if user has permission to view locations
        if not self.check_permission('view_locations_list', account):
            return Branch.objects.none()
        
        # Filter by account if we have one
        return Branch.objects.filter(account=account)
    
    def create(self, request, *args, **kwargs):
        """Override create to check manage_locations permission."""
        account = self.get_account_context()
        
        permission_error = self.require_permission('manage_locations', account)
        if permission_error:
            return permission_error
            
        return super().create(request, *args, **kwargs)
    
    def update(self, request, *args, **kwargs):
        """Override update to check manage_locations permission."""
        account = self.get_account_context()
        
        permission_error = self.require_permission('manage_locations', account)
        if permission_error:
            return permission_error
            
        return super().update(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        """Override destroy to check manage_locations permission."""
        account = self.get_account_context()
        
        permission_error = self.require_permission('manage_locations', account)
        if permission_error:
            return permission_error
            
        return super().destroy(request, *args, **kwargs)

class RoomViewSet(AccountPermissionMixin, viewsets.ModelViewSet):
    queryset = Room.objects.all()
    serializer_class = RoomSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['branch', 'is_active', 'is_private']
    search_fields = ['name']
    ordering_fields = ['name']
    
    def get_queryset(self):
        # Get account context
        account = self.get_account_context()
        
        if not account:
            # No account context - show rooms from all user's accounts
            if self.request.user.is_superuser:
                return Room.objects.all()
            else:
                user_accounts = AccountUser.objects.filter(
                    user=self.request.user,
                    is_active_in_account=True
                ).values_list('account', flat=True)
                branches = Branch.objects.filter(account__in=user_accounts).values_list('id', flat=True)
                return Room.objects.filter(branch__in=branches)
        
        # Check if user has permission to view rooms
        if not self.check_permission('view_rooms_list', account):
            return Room.objects.none()
        
        # Filter rooms by branches that belong to this account
        return Room.objects.filter(branch__account=account)
    
    def create(self, request, *args, **kwargs):
        """Override create to check manage_rooms permission."""
        account = self.get_account_context()
        
        permission_error = self.require_permission('manage_rooms', account)
        if permission_error:
            return permission_error
            
        return super().create(request, *args, **kwargs)
    
    def update(self, request, *args, **kwargs):
        """Override update to check manage_rooms permission."""
        account = self.get_account_context()
        
        permission_error = self.require_permission('manage_rooms', account)
        if permission_error:
            return permission_error
            
        return super().update(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        """Override destroy to check manage_rooms permission."""
        account = self.get_account_context()
        
        permission_error = self.require_permission('manage_rooms', account)
        if permission_error:
            return permission_error
            
        return super().destroy(request, *args, **kwargs)