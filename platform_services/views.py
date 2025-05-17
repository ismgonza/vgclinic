from django.shortcuts import render
# platform_services/views.py
from rest_framework import viewsets, permissions
from .models import Feature, Service, Plan
from .serializers import FeatureSerializer, ServiceSerializer, PlanSerializer


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Custom permission to allow only admins to edit, but anyone to read.
    """
    def has_permission(self, request, view):
        # Allow GET, HEAD, OPTIONS requests for any user
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions only for staff
        return request.user.is_staff


class FeatureViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows features to be viewed or edited.
    """
    queryset = Feature.objects.all()
    serializer_class = FeatureSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrReadOnly]
    filterset_fields = ['category', 'is_active']
    search_fields = ['name', 'code', 'description']
    ordering_fields = ['name', 'category', 'ui_order', 'created_at']


class ServiceViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows services to be viewed or edited.
    """
    queryset = Service.objects.all()
    serializer_class = ServiceSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrReadOnly]
    filterset_fields = ['is_active']
    search_fields = ['name', 'code', 'description']
    ordering_fields = ['name', 'ui_order', 'created_at']


class PlanViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows plans to be viewed or edited.
    """
    serializer_class = PlanSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrReadOnly]
    filterset_fields = ['is_active', 'is_public', 'is_featured', 'is_free']
    search_fields = ['name', 'code', 'description']
    ordering_fields = ['name', 'base_price', 'ui_order', 'created_at']
    
    def get_queryset(self):
        """
        Return all plans for staff, only public plans for non-staff.
        """
        if self.request.user.is_staff:
            return Plan.objects.all()
        return Plan.objects.filter(is_public=True, is_active=True)