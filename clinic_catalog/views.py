from django.shortcuts import render
# clinic_catalog/views.py
from rest_framework import viewsets, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import Category, CatalogItem, Package
from .serializers import (
    CategorySerializer, CatalogItemSerializer, CatalogItemListSerializer,
    PackageSerializer
)
from platform_accounts.permissions import IsAccountMember

class CategoryViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows categories to be viewed or edited.
    """
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticated, IsAccountMember]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active', 'parent']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'display_order', 'created_at']
    
    def get_queryset(self):
        """
        Filter categories based on the current user's permissions.
        """
        user = self.request.user
        account_id = self.request.query_params.get('account_id')
        
        if user.is_staff:
            queryset = Category.objects.all()
        else:
            # Only show categories for accounts the user is a member of
            queryset = Category.objects.filter(
                account__members__user=user,
                account__members__is_active=True
            )
        
        if account_id:
            queryset = queryset.filter(account_id=account_id)
            
        return queryset.order_by('display_order', 'name')


class CatalogItemViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows catalog items to be viewed or edited.
    """
    permission_classes = [permissions.IsAuthenticated, IsAccountMember]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active', 'category', 'item_type']
    search_fields = ['code', 'name', 'description']
    ordering_fields = ['code', 'name', 'price', 'created_at']
    
    def get_queryset(self):
        """
        Filter catalog items based on the current user's permissions.
        """
        user = self.request.user
        account_id = self.request.query_params.get('account_id')
        
        if user.is_staff:
            queryset = CatalogItem.objects.all()
        else:
            # Only show items for accounts the user is a member of
            queryset = CatalogItem.objects.filter(
                account__members__user=user,
                account__members__is_active=True
            )
        
        if account_id:
            queryset = queryset.filter(account_id=account_id)
            
        return queryset.order_by('code', 'name')
    
    def get_serializer_class(self):
        """
        Return different serializers for list and detail actions.
        """
        if self.action == 'list':
            return CatalogItemListSerializer
        return CatalogItemSerializer


class PackageViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows packages to be viewed or edited.
    """
    serializer_class = PackageSerializer
    permission_classes = [permissions.IsAuthenticated, IsAccountMember]
    
    def get_queryset(self):
        """
        Filter packages based on the current user's permissions.
        """
        user = self.request.user
        account_id = self.request.query_params.get('account_id')
        
        if user.is_staff:
            queryset = Package.objects.all()
        else:
            # Only show packages for accounts the user is a member of
            queryset = Package.objects.filter(
                catalog_item__account__members__user=user,
                catalog_item__account__members__is_active=True
            )
        
        if account_id:
            queryset = queryset.filter(catalog_item__account_id=account_id)
            
        return queryset.select_related('catalog_item').prefetch_related('package_items', 'package_items__item')