# clinic_catalog/serializers.py
from rest_framework import serializers
from .models import Category, CatalogItem, Package, PackageItem

class CategorySerializer(serializers.ModelSerializer):
    parent_name = serializers.CharField(source='parent.name', read_only=True, allow_null=True)
    subcategory_count = serializers.SerializerMethodField()
    item_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = [
            'id', 'account', 'name', 'description', 'parent', 'parent_name',
            'is_active', 'display_order', 'created_at', 'updated_at',
            'subcategory_count', 'item_count'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_subcategory_count(self, obj):
        return obj.subcategories.count()
    
    def get_item_count(self, obj):
        return obj.items.count()


class CatalogItemSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True, allow_null=True)
    account_name = serializers.CharField(source='account.name', read_only=True)
    
    class Meta:
        model = CatalogItem
        fields = [
            'id', 'account', 'account_name', 'code', 'name', 'description',
            'category', 'category_name', 'item_type', 'price', 'variable_price',
            'tax_rate', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class PackageItemSerializer(serializers.ModelSerializer):
    item_details = CatalogItemSerializer(source='item', read_only=True)
    
    class Meta:
        model = PackageItem
        fields = ['id', 'item', 'item_details', 'quantity']


class PackageSerializer(serializers.ModelSerializer):
    catalog_item_details = CatalogItemSerializer(source='catalog_item', read_only=True)
    package_items = PackageItemSerializer(many=True, read_only=True)
    included_items = serializers.PrimaryKeyRelatedField(
        many=True, 
        queryset=CatalogItem.objects.all(),
        write_only=True
    )
    
    class Meta:
        model = Package
        fields = [
            'id', 'catalog_item', 'catalog_item_details', 'package_items',
            'included_items', 'discount_type', 'discount_value'
        ]
    
    def create(self, validated_data):
        included_items = validated_data.pop('included_items')
        package = super().create(validated_data)
        
        # Add the included items
        for item in included_items:
            PackageItem.objects.create(package=package, item=item)
        
        return package
    
    def update(self, instance, validated_data):
        if 'included_items' in validated_data:
            included_items = validated_data.pop('included_items')
            
            # Clear existing items
            instance.package_items.all().delete()
            
            # Add new items
            for item in included_items:
                PackageItem.objects.create(package=instance, item=item)
        
        return super().update(instance, validated_data)


class CatalogItemListSerializer(serializers.ModelSerializer):
    """
    A simplified serializer for list views.
    """
    category_name = serializers.CharField(source='category.name', read_only=True, allow_null=True)
    
    class Meta:
        model = CatalogItem
        fields = [
            'id', 'code', 'name', 'item_type', 'price',
            'category_name', 'is_active'
        ]