# platform_services/serializers.py
from rest_framework import serializers
from .models import Feature, Service, Plan

class FeatureSerializer(serializers.ModelSerializer):
    class Meta:
        model = Feature
        fields = [
            'id', 'name', 'code', 'description', 'category', 'is_active',
            'icon', 'ui_order', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class ServiceSerializer(serializers.ModelSerializer):
    features_details = FeatureSerializer(source='features', many=True, read_only=True)
    
    class Meta:
        model = Service
        fields = [
            'id', 'name', 'code', 'description', 'features', 'features_details',
            'is_active', 'icon', 'ui_order', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class PlanSerializer(serializers.ModelSerializer):
    services_details = ServiceSerializer(source='services', many=True, read_only=True)
    features_details = FeatureSerializer(source='features', many=True, read_only=True)
    all_features_list = FeatureSerializer(source='all_features', many=True, read_only=True)
    
    class Meta:
        model = Plan
        fields = [
            'id', 'name', 'code', 'description', 'services', 'services_details',
            'features', 'features_details', 'all_features_list', 'is_free', 'base_price',
            'billing_period', 'max_users', 'max_locations', 'max_storage_gb',
            'is_featured', 'is_public', 'ui_order', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']