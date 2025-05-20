# clinic_locations/views.py
from rest_framework import viewsets, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend
from platform_accounts.models import AccountUser
from .models import Branch, Room
from .serializers import BranchSerializer, RoomSerializer

# Custom permission to check if user has access to the branch's account
class HasBranchAccess(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        # Check if user is superuser
        if request.user.is_superuser:
            return True
        
        # For Branch objects
        if isinstance(obj, Branch):
            account = obj.account
        # For Room objects
        elif isinstance(obj, Room):
            account = obj.branch.account
        else:
            return False
            
        # Check if user has access to the account
        return AccountUser.objects.filter(
            user=request.user,
            account=account,
            is_active_in_account=True
        ).exists()

class BranchViewSet(viewsets.ModelViewSet):
    queryset = Branch.objects.all()
    serializer_class = BranchSerializer
    permission_classes = [permissions.IsAuthenticated, HasBranchAccess]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['account', 'is_active', 'province']
    search_fields = ['name', 'email', 'phone', 'address']
    ordering_fields = ['name', 'province']
    
    def get_queryset(self):
        # If superuser, return all
        if self.request.user.is_superuser:
            return Branch.objects.all()
            
        # Otherwise, return branches for accounts the user has access to
        user_accounts = AccountUser.objects.filter(
            user=self.request.user,
            is_active_in_account=True
        ).values_list('account', flat=True)
        
        return Branch.objects.filter(account__in=user_accounts)

class RoomViewSet(viewsets.ModelViewSet):
    queryset = Room.objects.all()
    serializer_class = RoomSerializer
    permission_classes = [permissions.IsAuthenticated, HasBranchAccess]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['branch', 'is_active', 'is_private']
    search_fields = ['name']
    ordering_fields = ['name']
    
    def get_queryset(self):
        # If superuser, return all
        if self.request.user.is_superuser:
            return Room.objects.all()
            
        # Otherwise, return rooms for branches in accounts the user has access to
        user_accounts = AccountUser.objects.filter(
            user=self.request.user,
            is_active_in_account=True
        ).values_list('account', flat=True)
        
        branches = Branch.objects.filter(account__in=user_accounts).values_list('id', flat=True)
        
        return Room.objects.filter(branch__in=branches)