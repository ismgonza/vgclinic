# platform_contracts/views.py
from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from .models import Contract, FeatureOverride, UsageQuota
from .serializers import (
    ContractSerializer, FeatureOverrideSerializer, UsageQuotaSerializer
)

class ContractViewSet(viewsets.ModelViewSet):
    queryset = Contract.objects.all()
    serializer_class = ContractSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['contract_type', 'status', 'is_trial', 'auto_renew', 'plan']
    search_fields = ['contract_number', 'account__account_name', 'user__email', 'notes']
    ordering_fields = ['start_date', 'end_date']
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        contract = self.get_object()
        
        # Update status to 'terminated'
        contract.status = 'terminated'
        contract.auto_renew = False
        
        # Set reason if provided
        reason = request.data.get('reason', '')
        if reason:
            contract.notes += f"\n\nCancellation Reason ({timezone.now().strftime('%Y-%m-%d')}): {reason}"
        
        contract.save()
        serializer = self.get_serializer(contract)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def renew(self, request, pk=None):
        contract = self.get_object()
        
        # Check if contract is eligible for renewal
        if contract.end_date and contract.end_date > timezone.now():
            return Response(
                {'error': 'Contract cannot be renewed before its end date'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update status to 'active'
        contract.status = 'active'
        
        # Set new dates
        contract.start_date = timezone.now()
        
        # Calculate new end date based on billing period
        if contract.billing_period == 'monthly':
            contract.end_date = contract.start_date + timezone.timedelta(days=30)
        elif contract.billing_period == 'quarterly':
            contract.end_date = contract.start_date + timezone.timedelta(days=90)
        elif contract.billing_period == 'biannual':
            contract.end_date = contract.start_date + timezone.timedelta(days=180)
        elif contract.billing_period == 'annual':
            contract.end_date = contract.start_date + timezone.timedelta(days=365)
        
        contract.save()
        serializer = self.get_serializer(contract)
        return Response(serializer.data)

class FeatureOverrideViewSet(viewsets.ModelViewSet):
    queryset = FeatureOverride.objects.all()
    serializer_class = FeatureOverrideSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['contract', 'override_type']
    search_fields = ['feature_code', 'reason']
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

class UsageQuotaViewSet(viewsets.ModelViewSet):
    queryset = UsageQuota.objects.all()
    serializer_class = UsageQuotaSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['contract', 'quota_type']
    
    @action(detail=True, methods=['post'])
    def update_usage(self, request, pk=None):
        quota = self.get_object()
        usage = request.data.get('usage', None)
        
        if usage is None:
            return Response(
                {'error': 'Usage value is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            usage = int(usage)
            quota.current_usage = usage
            quota.save()
            serializer = self.get_serializer(quota)
            return Response(serializer.data)
        except ValueError:
            return Response(
                {'error': 'Invalid usage value. Must be an integer.'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def increment_usage(self, request, pk=None):
        quota = self.get_object()
        amount = request.data.get('amount', 1)
        
        try:
            amount = int(amount)
            quota.current_usage += amount
            quota.save()
            serializer = self.get_serializer(quota)
            return Response(serializer.data)
        except ValueError:
            return Response(
                {'error': 'Invalid amount value. Must be an integer.'},
                status=status.HTTP_400_BAD_REQUEST
            )