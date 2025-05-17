# clinic_staff/serializers.py
from rest_framework import serializers
from .models import StaffSpecialty, StaffMember, StaffLocation, AvailabilitySchedule
from platform_users.serializers import UserSerializer
from platform_accounts.serializers import AccountUserSerializer
from clinic_locations.serializers import LocationMinimalSerializer

class StaffSpecialtySerializer(serializers.ModelSerializer):
    account_name = serializers.CharField(source='account.name', read_only=True)
    
    class Meta:
        model = StaffSpecialty
        fields = [
            'id', 'account', 'account_name', 'name', 'description',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class StaffLocationSerializer(serializers.ModelSerializer):
    location_details = LocationMinimalSerializer(source='location', read_only=True)
    
    class Meta:
        model = StaffLocation
        fields = [
            'id', 'staff', 'location', 'location_details', 'is_primary', 'created_at'
        ]
        read_only_fields = ['created_at']


class AvailabilityScheduleSerializer(serializers.ModelSerializer):
    day_name = serializers.CharField(source='get_day_of_week_display', read_only=True)
    location_name = serializers.CharField(source='location.name', read_only=True)
    
    class Meta:
        model = AvailabilitySchedule
        fields = [
            'id', 'staff', 'location', 'location_name', 'day_of_week', 'day_name',
            'start_time', 'end_time', 'is_available'
        ]


class StaffMemberSerializer(serializers.ModelSerializer):
    user_details = serializers.SerializerMethodField()
    account_details = serializers.SerializerMethodField()
    role_display = serializers.CharField(source='get_staff_role_display', read_only=True)
    specialties_details = StaffSpecialtySerializer(source='specialties', many=True, read_only=True)
    assigned_locations_details = serializers.SerializerMethodField()
    availability_schedules_details = AvailabilityScheduleSerializer(source='availability_schedules', many=True, read_only=True)
    
    class Meta:
        model = StaffMember
        fields = [
            'id', 'account_user', 'user_details', 'account_details',
            'job_title', 'staff_role', 'role_display', 'specialties',
            'specialties_details', 'license_number', 'phone',
            'is_active', 'can_book_appointments', 'appointment_color',
            'assigned_locations_details', 'availability_schedules_details',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_user_details(self, obj):
        user = obj.account_user.user
        return {
            'id': user.id,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'full_name': f"{user.first_name} {user.last_name}"
        }
    
    def get_account_details(self, obj):
        account = obj.account_user.account
        return {
            'id': account.id,
            'name': account.name,
            'slug': account.slug
        }
    
    def get_assigned_locations_details(self, obj):
        locations = StaffLocation.objects.filter(staff=obj)
        return StaffLocationSerializer(locations, many=True).data


class StaffMemberListSerializer(serializers.ModelSerializer):
    """
    A simplified serializer for list views.
    """
    full_name = serializers.SerializerMethodField()
    role_display = serializers.CharField(source='get_staff_role_display', read_only=True)
    account_name = serializers.CharField(source='account_user.account.name', read_only=True)
    
    class Meta:
        model = StaffMember
        fields = [
            'id', 'full_name', 'job_title', 'staff_role', 'role_display',
            'appointment_color', 'account_name', 'is_active'
        ]
    
    def get_full_name(self, obj):
        user = obj.account_user.user
        return f"{user.first_name} {user.last_name}"