# clinic_locations/serializers.py
from rest_framework import serializers
from .models import Location, Room

class RoomSerializer(serializers.ModelSerializer):
    location_name = serializers.CharField(source='location.name', read_only=True)
    
    class Meta:
        model = Room
        fields = [
            'id', 'location', 'location_name', 'name', 
            'is_active', 'is_private', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class LocationSerializer(serializers.ModelSerializer):
    rooms = RoomSerializer(many=True, read_only=True)
    account_name = serializers.CharField(source='account.name', read_only=True)
    
    class Meta:
        model = Location
        fields = [
            'id', 'account', 'account_name', 'name', 'email', 'phone',
            'province', 'canton', 'district', 'address',
            'is_active', 'created_at', 'updated_at', 'rooms'
        ]
        read_only_fields = ['created_at', 'updated_at']


class LocationMinimalSerializer(serializers.ModelSerializer):
    """
    A simplified version of LocationSerializer for dropdown lists.
    """
    class Meta:
        model = Location
        fields = ['id', 'name', 'province', 'canton']