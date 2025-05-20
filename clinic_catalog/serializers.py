# clinic_catalog/serializers.py
from rest_framework import serializers
from .models import Specialty, CatalogItem
from platform_accounts.serializers import AccountSerializer

class SpecialtySerializer(serializers.ModelSerializer):
    account_details = AccountSerializer(source='account', read_only=True)
    
    class Meta:
        model = Specialty
        fields = ('id', 'account', 'name', 'code', 'description', 
                  'is_active', 'created_at', 'updated_at', 'account_details')
        read_only_fields = ('created_at', 'updated_at')

class CatalogItemSerializer(serializers.ModelSerializer):
    specialty_details = SpecialtySerializer(source='specialty', read_only=True)
    account_details = AccountSerializer(source='account', read_only=True)
    
    class Meta:
        model = CatalogItem
        fields = ('id', 'account', 'specialty', 'code', 'name', 'description',
                  'price', 'is_variable_price', 'is_active', 'created_at', 
                  'updated_at', 'specialty_details', 'account_details')
        read_only_fields = ('created_at', 'updated_at')