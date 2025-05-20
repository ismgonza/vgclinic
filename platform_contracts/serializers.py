# platform_contracts/serializers.py
from rest_framework import serializers
from .models import ContractStatus, Contract, FeatureOverride, UsageQuota
from platform_accounts.serializers import AccountSerializer
from platform_users.serializers import UserSerializer
from platform_services.serializers import PlanSerializer

class ContractStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContractStatus
        fields = ('code', 'name', 'description')

class FeatureOverrideSerializer(serializers.ModelSerializer):
    class Meta:
        model = FeatureOverride
        fields = ('id', 'contract', 'feature_code', 'override_type', 
                  'reason', 'created_by', 'created_at', 'expires_at')
        read_only_fields = ('created_at',)

class UsageQuotaSerializer(serializers.ModelSerializer):
    percentage_used = serializers.FloatField(read_only=True, source='percentage_used')
    is_exceeded = serializers.BooleanField(read_only=True, source='is_exceeded')
    
    class Meta:
        model = UsageQuota
        fields = ('id', 'contract', 'quota_type', 'limit', 'current_usage', 
                  'created_at', 'updated_at', 'percentage_used', 'is_exceeded')
        read_only_fields = ('created_at', 'updated_at')

class ContractSerializer(serializers.ModelSerializer):
    status_details = ContractStatusSerializer(source='status', read_only=True)
    plan_details = PlanSerializer(source='plan', read_only=True)
    account_details = AccountSerializer(source='account', read_only=True)
    user_details = UserSerializer(source='user', read_only=True)
    feature_overrides = FeatureOverrideSerializer(many=True, read_only=True)
    quotas = UsageQuotaSerializer(many=True, read_only=True)
    is_active = serializers.BooleanField(read_only=True, source='is_active')
    
    class Meta:
        model = Contract
        fields = ('contract_number', 'plan', 'contract_type', 'account', 'user',
                  'status', 'is_trial', 'start_date', 'end_date', 
                  'price_override', 'billing_period', 'auto_renew', 'notes',
                  'created_by', 'created_at', 'updated_at', 'status_details',
                  'plan_details', 'account_details', 'user_details',
                  'feature_overrides', 'quotas', 'is_active')
        read_only_fields = ('created_at', 'updated_at', 'created_by')