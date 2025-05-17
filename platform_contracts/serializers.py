# platform_contracts/serializers.py
from rest_framework import serializers
from .models import Subscription, FeatureOverride, UsageQuota, Invoice, InvoiceItem
from platform_accounts.serializers import AccountSerializer
from platform_services.serializers import PlanSerializer
from platform_users.serializers import UserSerializer

class FeatureOverrideSerializer(serializers.ModelSerializer):
    class Meta:
        model = FeatureOverride
        fields = [
            'id', 'subscription', 'feature_code', 'override_type', 
            'reason', 'created_by', 'created_at', 'expires_at'
        ]
        read_only_fields = ['created_at']


class UsageQuotaSerializer(serializers.ModelSerializer):
    percentage_used = serializers.FloatField(read_only=True)
    is_exceeded = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = UsageQuota
        fields = [
            'id', 'subscription', 'quota_type', 'limit', 
            'current_usage', 'percentage_used', 'is_exceeded',
            'reset_date', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class InvoiceItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = InvoiceItem
        fields = [
            'id', 'invoice', 'description', 'quantity', 
            'unit_price', 'amount'
        ]


class InvoiceSerializer(serializers.ModelSerializer):
    items = InvoiceItemSerializer(many=True, read_only=True)
    
    class Meta:
        model = Invoice
        fields = [
            'id', 'subscription', 'invoice_number', 'status',
            'amount', 'tax_amount', 'total_amount', 'issue_date',
            'due_date', 'paid_date', 'payment_method', 'payment_reference',
            'notes', 'created_at', 'updated_at', 'items'
        ]
        read_only_fields = ['created_at', 'updated_at']


class SubscriptionSerializer(serializers.ModelSerializer):
    account_details = AccountSerializer(source='account', read_only=True)
    plan_details = PlanSerializer(source='plan', read_only=True)
    created_by_details = UserSerializer(source='created_by', read_only=True)
    feature_overrides = FeatureOverrideSerializer(many=True, read_only=True)
    quotas = UsageQuotaSerializer(many=True, read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Subscription
        fields = [
            'id', 'account', 'account_details', 'plan', 'plan_details',
            'status', 'start_date', 'end_date', 'trial_end', 'canceled_at',
            'is_paid', 'next_billing_date', 'billing_period', 'price_override',
            'auto_renew', 'cancellation_reason', 'notes', 'payment_provider',
            'external_id', 'created_by', 'created_by_details', 'created_at',
            'updated_at', 'feature_overrides', 'quotas', 'is_active'
        ]
        read_only_fields = ['created_at', 'updated_at']


class SubscriptionCancelSerializer(serializers.Serializer):
    reason = serializers.CharField(required=False, allow_blank=True)