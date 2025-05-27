# platform_accounts/serializers.py
from rest_framework import serializers
from .models import Account, AccountOwner, AccountUser
from platform_users.serializers import UserSerializer

class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = ('account_id', 'account_name', 'account_logo', 'account_website',
                  'account_email', 'account_phone', 'account_address',
                  'account_status', 'is_platform_account', 'account_created_at')
        read_only_fields = ('account_id', 'account_created_at')

class AccountOwnerSerializer(serializers.ModelSerializer):
    user_details = UserSerializer(source='user', read_only=True)
    account_details = AccountSerializer(source='account', read_only=True)
    
    class Meta:
        model = AccountOwner
        fields = ('id', 'user', 'account', 'is_active', 'created_at', 
                  'user_details', 'account_details')
        read_only_fields = ('id', 'created_at')

class AccountUserSerializer(serializers.ModelSerializer):
    user_details = UserSerializer(source='user', read_only=True)
    account_details = AccountSerializer(source='account', read_only=True)
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    specialty_details = serializers.SerializerMethodField()
    
    class Meta:
        model = AccountUser
        fields = ('id', 'user', 'account', 'role', 'role_display', 'specialty', 
                  'specialty_details', 'color', 'phone_number', 'is_active_in_account', 
                  'created_at', 'user_details', 'account_details')
        read_only_fields = ('id', 'created_at')
    
    def get_specialty_details(self, obj):
        if obj.specialty:
            from clinic_catalog.serializers import SpecialtySerializer
            return SpecialtySerializer(obj.specialty).data
        return None