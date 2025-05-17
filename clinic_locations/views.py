from django.shortcuts import render
# clinic_locations/views.py
from rest_framework import viewsets, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import Location, Room
from .serializers import LocationSerializer, LocationMinimalSerializer, RoomSerializer
from platform_accounts.permissions import IsAccountMember

class LocationViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows locations to be viewed or edited.
    """
    serializer_class = LocationSerializer
    permission_classes = [permissions.IsAuthenticated, IsAccountMember]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active', 'province', 'canton']
    search_fields = ['name', 'email', 'phone', 'address']
    ordering_fields = ['name', 'created_at']
    
    def get_queryset(self):
        """
        Filter locations based on the current user's permissions.
        """
        user = self.request.user
        account_id = self.request.query_params.get('account_id')
        
        if user.is_staff:
            queryset = Location.objects.all()
        else:
            # Only show locations for accounts the user is a member of
            queryset = Location.objects.filter(
                account__members__user=user,
                account__members__is_active=True
            )
        
        if account_id:
            queryset = queryset.filter(account_id=account_id)
            
        return queryset.order_by('name')
    
    def get_serializer_class(self):
        """
        Return a minimal serializer for list actions.
        """
        if self.action == 'list' and self.request.query_params.get('minimal') == 'true':
            return LocationMinimalSerializer
        return LocationSerializer
    
    def perform_create(self, serializer):
        """
        When creating a location, check if the account has reached its location quota.
        """
        account = serializer.validated_data['account']
        
        # Check if account has an active subscription
        active_subscription = account.subscriptions.filter(
            status__in=['active', 'trialing']
        ).first()
        
        if active_subscription:
            # Check if location quota exists
            location_quota = active_subscription.quotas.filter(quota_type='locations').first()
            
            if location_quota:
                # Count current locations
                current_locations = Location.objects.filter(account=account).count()
                
                # Check if quota would be exceeded
                if current_locations >= location_quota.limit:
                    from rest_framework.exceptions import PermissionDenied
                    raise PermissionDenied("Location quota exceeded for this account.")
        
        serializer.save()


class RoomViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows rooms to be viewed or edited.
    """
    serializer_class = RoomSerializer
    permission_classes = [permissions.IsAuthenticated, IsAccountMember]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active', 'is_private', 'location']
    search_fields = ['name']
    ordering_fields = ['name', 'created_at']
    
    def get_queryset(self):
        """
        Filter rooms based on the current user's permissions.
        """
        user = self.request.user
        location_id = self.request.query_params.get('location_id')
        
        if user.is_staff:
            queryset = Room.objects.all()
        else:
            # Only show rooms for locations in accounts the user is a member of
            queryset = Room.objects.filter(
                location__account__members__user=user,
                location__account__members__is_active=True
            )
        
        if location_id:
            queryset = queryset.filter(location_id=location_id)
            
        return queryset.order_by('location', 'name')