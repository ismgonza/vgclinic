# platform_accounts/serializers.py
from rest_framework import serializers
from .models import Account, Role, AccountUser
from platform_users.serializers import UserSerializer

class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ('id', 'role_name', 'role_description')

class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = ('account_id', 'account_name', 'account_logo', 'account_website',
                  'account_email', 'account_phone', 'account_address',
                  'account_status', 'is_platform_account', 'account_created_at')
        read_only_fields = ('account_id', 'account_created_at')

class AccountUserSerializer(serializers.ModelSerializer):
    user_details = UserSerializer(source='user', read_only=True)
    account_details = AccountSerializer(source='account', read_only=True)
    role_details = RoleSerializer(source='role', read_only=True)
    
    class Meta:
        model = AccountUser
        fields = ('id', 'user', 'account', 'role', 'color', 'phone_number',
                  'is_active_in_account', 'created_at', 'user_details',
                  'account_details', 'role_details')
        read_only_fields = ('id', 'created_at')