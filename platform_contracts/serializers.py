# platform_contracts/serializers.py
from rest_framework import serializers
from .models import Contract, FeatureOverride, UsageQuota
from platform_accounts.serializers import AccountSerializer
from platform_users.serializers import UserSerializer
from platform_services.serializers import PlanSerializer

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
    plan_details = PlanSerializer(source='plan', read_only=True)
    account_details = AccountSerializer(source='account', read_only=True)
    user_details = UserSerializer(source='user', read_only=True)
    feature_overrides = serializers.SerializerMethodField()
    quotas = serializers.SerializerMethodField()
    is_active = serializers.BooleanField(read_only=True)
    
    # Make contract_number read-only since it's auto-generated
    contract_number = serializers.CharField(read_only=True)
    
    class Meta:
        model = Contract
        fields = ('contract_number', 'plan', 'contract_type', 'account', 'user',
                  'status', 'is_trial', 'start_date', 'end_date', 
                  'price_override', 'billing_period', 'auto_renew', 'notes',
                  'created_by', 'created_at', 'updated_at',
                  'plan_details', 'account_details', 'user_details',
                  'feature_overrides', 'quotas', 'is_active')
        read_only_fields = ('contract_number', 'created_at', 'updated_at', 'created_by')
    
    def get_feature_overrides(self, obj):
        from .serializers import FeatureOverrideSerializer
        overrides = FeatureOverride.objects.filter(contract=obj)
        return FeatureOverrideSerializer(overrides, many=True).data
    
    def get_quotas(self, obj):
        from .serializers import UsageQuotaSerializer
        quotas = UsageQuota.objects.filter(contract=obj)
        return UsageQuotaSerializer(quotas, many=True).data
    
    def validate(self, data):
        """
        Check that the contract has either an account or user based on contract_type
        """
        contract_type = data.get('contract_type')
        account = data.get('account')
        user = data.get('user')
        
        if contract_type == 'account' and not account:
            raise serializers.ValidationError({
                'account': 'Account is required for account contracts.'
            })
        
        if contract_type == 'user' and not user:
            raise serializers.ValidationError({
                'user': 'User is required for user contracts.'
            })
        
        return data