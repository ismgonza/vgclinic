from django.shortcuts import render
# platform_contracts/views.py
from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from django.db import transaction

from .models import Subscription, FeatureOverride, UsageQuota, Invoice, InvoiceItem
from .serializers import (
    SubscriptionSerializer, FeatureOverrideSerializer, UsageQuotaSerializer,
    InvoiceSerializer, InvoiceItemSerializer, SubscriptionCancelSerializer
)
from platform_accounts.permissions import IsAccountOwnerOrAdmin


class SubscriptionViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows subscriptions to be viewed or edited.
    """
    serializer_class = SubscriptionSerializer
    permission_classes = [permissions.IsAuthenticated, IsAccountOwnerOrAdmin]
    filterset_fields = ['status', 'auto_renew', 'is_paid']
    search_fields = ['account__name', 'plan__name', 'notes']
    ordering_fields = ['start_date', 'end_date', 'created_at']
    
    def get_queryset(self):
        """
        Filter subscriptions based on the current user's permissions.
        """
        user = self.request.user
        account_id = self.request.query_params.get('account_id')
        
        if user.is_staff:
            queryset = Subscription.objects.all()
        else:
            # Only show subscriptions for accounts where user is admin
            queryset = Subscription.objects.filter(
                account__members__user=user,
                account__members__role__in=['admin', 'owner']
            )
        
        if account_id:
            queryset = queryset.filter(account_id=account_id)
            
        return queryset.order_by('-start_date')
    
    def perform_create(self, serializer):
        """
        When creating a subscription, set the current user as created_by.
        Also create default usage quotas based on the plan limits.
        """
        with transaction.atomic():
            subscription = serializer.save(created_by=self.request.user)
            plan = subscription.plan
            
            # Create usage quotas
            UsageQuota.objects.create(
                subscription=subscription,
                quota_type='users',
                limit=plan.max_users
            )
            
            UsageQuota.objects.create(
                subscription=subscription,
                quota_type='locations',
                limit=plan.max_locations
            )
            
            UsageQuota.objects.create(
                subscription=subscription,
                quota_type='storage',
                limit=plan.max_storage_gb
            )
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """
        Cancel a subscription.
        """
        subscription = self.get_object()
        serializer = SubscriptionCancelSerializer(data=request.data)
        
        if serializer.is_valid():
            reason = serializer.validated_data.get('reason', '')
            subscription.cancel(reason=reason)
            return Response({'status': 'subscription canceled'})
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class FeatureOverrideViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows feature overrides to be viewed or edited.
    """
    serializer_class = FeatureOverrideSerializer
    permission_classes = [permissions.IsAuthenticated, IsAccountOwnerOrAdmin]
    filterset_fields = ['override_type', 'feature_code']
    
    def get_queryset(self):
        """
        Filter feature overrides based on the current user's permissions.
        """
        user = self.request.user
        subscription_id = self.request.query_params.get('subscription_id')
        
        if user.is_staff:
            queryset = FeatureOverride.objects.all()
        else:
            queryset = FeatureOverride.objects.filter(
                subscription__account__members__user=user,
                subscription__account__members__role__in=['admin', 'owner']
            )
        
        if subscription_id:
            queryset = queryset.filter(subscription_id=subscription_id)
            
        return queryset
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class UsageQuotaViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows usage quotas to be viewed or edited.
    """
    serializer_class = UsageQuotaSerializer
    permission_classes = [permissions.IsAuthenticated, IsAccountOwnerOrAdmin]
    filterset_fields = ['quota_type']
    
    def get_queryset(self):
        """
        Filter usage quotas based on the current user's permissions.
        """
        user = self.request.user
        subscription_id = self.request.query_params.get('subscription_id')
        
        if user.is_staff:
            queryset = UsageQuota.objects.all()
        else:
            queryset = UsageQuota.objects.filter(
                subscription__account__members__user=user,
                subscription__account__members__role__in=['admin', 'owner']
            )
        
        if subscription_id:
            queryset = queryset.filter(subscription_id=subscription_id)
            
        return queryset


class InvoiceViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows invoices to be viewed or edited.
    """
    serializer_class = InvoiceSerializer
    permission_classes = [permissions.IsAuthenticated, IsAccountOwnerOrAdmin]
    filterset_fields = ['status']
    
    def get_queryset(self):
        """
        Filter invoices based on the current user's permissions.
        """
        user = self.request.user
        subscription_id = self.request.query_params.get('subscription_id')
        account_id = self.request.query_params.get('account_id')
        
        if user.is_staff:
            queryset = Invoice.objects.all()
        else:
            queryset = Invoice.objects.filter(
                subscription__account__members__user=user,
                subscription__account__members__role__in=['admin', 'owner']
            )
        
        if subscription_id:
            queryset = queryset.filter(subscription_id=subscription_id)
            
        if account_id:
            queryset = queryset.filter(subscription__account_id=account_id)
            
        return queryset.order_by('-issue_date')


class InvoiceItemViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows invoice items to be viewed or edited.
    """
    serializer_class = InvoiceItemSerializer
    permission_classes = [permissions.IsAuthenticated, IsAccountOwnerOrAdmin]
    
    def get_queryset(self):
        """
        Filter invoice items based on the current user's permissions.
        """
        user = self.request.user
        invoice_id = self.request.query_params.get('invoice_id')
        
        if user.is_staff:
            queryset = InvoiceItem.objects.all()
        else:
            queryset = InvoiceItem.objects.filter(
                invoice__subscription__account__members__user=user,
                invoice__subscription__account__members__role__in=['admin', 'owner']
            )
        
        if invoice_id:
            queryset = queryset.filter(invoice_id=invoice_id)
            
        return queryset