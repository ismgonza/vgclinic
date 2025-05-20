# clinic_locations/serializers.py
from rest_framework import serializers
from .models import Branch, Room
from platform_accounts.serializers import AccountSerializer

class RoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Room
        fields = ('id', 'branch', 'name', 'is_active', 'is_private', 'created_at', 'updated_at')
        read_only_fields = ('created_at', 'updated_at')

class BranchSerializer(serializers.ModelSerializer):
    rooms = RoomSerializer(many=True, read_only=True)
    account_details = AccountSerializer(source='account', read_only=True)
    
    class Meta:
        model = Branch
        fields = ('id', 'account', 'name', 'email', 'phone', 'province', 'canton', 
                  'district', 'address', 'is_active', 'created_at', 'updated_at', 
                  'rooms', 'account_details')
        read_only_fields = ('created_at', 'updated_at')