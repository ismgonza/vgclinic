# clinic_locations/views.py
from rest_framework import viewsets, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend
from platform_accounts.models import Account, AccountUser
from .models import Branch, Room
from .serializers import BranchSerializer, RoomSerializer

class BranchViewSet(viewsets.ModelViewSet):
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
        
        # Start with base queryset
        queryset = Branch.objects.all()
        
        # Filter by account if we have one
        if account:
            queryset = queryset.filter(account=account)
        else:
            print("DEBUG: No account context - showing all branches user has access to")
            # Fallback: show branches for accounts the user has access to
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

class RoomViewSet(viewsets.ModelViewSet):
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
        
        # Start with base queryset
        queryset = Room.objects.all()
        
        # Filter by account if we have one
        if account:
            # Filter rooms by branches that belong to this account
            queryset = queryset.filter(branch__account=account)
        else:
            print("DEBUG: No account context - showing all rooms user has access to")
            # Fallback: show rooms for accounts the user has access to
            if not self.request.user.is_superuser:
                user_accounts = AccountUser.objects.filter(
                    user=self.request.user,
                    is_active_in_account=True
                ).values_list('account', flat=True)
                branches = Branch.objects.filter(account__in=user_accounts).values_list('id', flat=True)
                queryset = queryset.filter(branch__in=branches)
        
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