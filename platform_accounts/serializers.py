# platform_accounts/serializers.py
from rest_framework import serializers
from .models import Account, AccountUser, AccountInvitation
from platform_users.serializers import UserSerializer

class AccountSerializer(serializers.ModelSerializer):
    owner_details = UserSerializer(source='owner', read_only=True)
    
    class Meta:
        model = Account
        fields = [
            'id', 'name', 'slug', 'description', 'logo', 'website', 
            'email', 'phone', 'address', 'status', 'created_at', 
            'updated_at', 'owner', 'owner_details'
        ]
        read_only_fields = ['created_at', 'updated_at']


class AccountUserSerializer(serializers.ModelSerializer):
    user_details = UserSerializer(source='user', read_only=True)
    account_name = serializers.CharField(source='account.name', read_only=True)
    
    class Meta:
        model = AccountUser
        fields = [
            'id', 'account', 'account_name', 'user', 'user_details',
            'role', 'is_active', 'joined_at'
        ]
        read_only_fields = ['joined_at']


class AccountInvitationSerializer(serializers.ModelSerializer):
    account_name = serializers.CharField(source='account.name', read_only=True)
    invited_by_name = serializers.CharField(source='invited_by.full_name', read_only=True)
    
    class Meta:
        model = AccountInvitation
        fields = [
            'id', 'account', 'account_name', 'email', 'role', 'status',
            'invited_by', 'invited_by_name', 'created_at', 'expires_at'
        ]
        read_only_fields = ['invitation_code', 'created_at']