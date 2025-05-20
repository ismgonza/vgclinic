# platform_services/serializers.py
from rest_framework import serializers
from .models import Feature, Service, Plan

class FeatureSerializer(serializers.ModelSerializer):
    class Meta:
        model = Feature
        fields = ('id', 'name', 'code', 'description', 'category', 
                  'icon', 'ui_order', 'is_active', 'created_at', 'updated_at')
        read_only_fields = ('created_at', 'updated_at')

class ServiceSerializer(serializers.ModelSerializer):
    features_list = FeatureSerializer(source='features', many=True, read_only=True)
    
    class Meta:
        model = Service
        fields = ('id', 'name', 'code', 'description', 'features', 
                  'icon', 'ui_order', 'is_active', 'created_at', 
                  'updated_at', 'features_list')
        read_only_fields = ('created_at', 'updated_at')

class PlanSerializer(serializers.ModelSerializer):
    services_list = ServiceSerializer(source='services', many=True, read_only=True)
    features_list = FeatureSerializer(source='features', many=True, read_only=True)
    all_features_list = FeatureSerializer(source='all_features', many=True, read_only=True)
    
    class Meta:
        model = Plan
        fields = ('id', 'name', 'code', 'description', 'plan_type', 
                  'services', 'features', 'base_price', 'billing_period', 
                  'max_users', 'max_locations', 'ui_order', 'is_active', 
                  'created_at', 'updated_at', 'services_list', 
                  'features_list', 'all_features_list')
        read_only_fields = ('created_at', 'updated_at', 'all_features')