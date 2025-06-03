# platform_users/serializers.py
from rest_framework import serializers
from .models import User

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'email', 'first_name', 'last_name', 'id_type', 'id_number', 'is_active', 'is_staff', 'is_superuser')
        read_only_fields = ('id', 'email', 'is_staff', 'is_superuser')
        extra_kwargs = {
            'password': {'write_only': True}
        }
    
    def create(self, validated_data):
        # Handle password correctly
        password = validated_data.pop('password', None)
        user = User.objects.create(**validated_data)
        if password:
            user.set_password(password)
            user.save()
        return user

# NEW: Serializer for profile updates (limited fields)
class ProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('first_name', 'last_name')
        
    def validate_first_name(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("First name is required.")
        return value.strip()
    
    def validate_last_name(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Last name is required.")
        return value.strip()

# NEW: Serializer for password change
class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, min_length=8)
    
    def validate_current_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Current password is incorrect.")
        return value
    
    def validate_new_password(self, value):
        if len(value) < 8:
            raise serializers.ValidationError("New password must be at least 8 characters long.")
        return value

# UPDATED: Serializer for detailed profile view (includes AccountUser info)
class ProfileDetailSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    # NEW: AccountUser fields
    phone_number = serializers.SerializerMethodField()
    role = serializers.SerializerMethodField()
    role_display = serializers.SerializerMethodField()
    specialty = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ('id', 'email', 'first_name', 'last_name', 'full_name', 
                 'id_type', 'id_number', 'is_active', 'is_staff', 'is_superuser', 
                 'date_joined', 'last_login',
                 # NEW: AccountUser fields
                 'phone_number', 'role', 'role_display', 'specialty')
        read_only_fields = ('id', 'email', 'id_type', 'id_number', 'is_active', 
                           'is_staff', 'is_superuser', 'date_joined', 'last_login')
    
    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip()
    
    def get_phone_number(self, obj):
        """Get phone_number from AccountUser based on account context"""
        request = self.context.get('request')
        if not request:
            return None
            
        # Get account_id from header
        account_id = request.headers.get('X-Account-Context')
        if not account_id:
            return None
            
        try:
            from platform_accounts.models import AccountUser
            account_user = AccountUser.objects.get(
                user=obj,
                account__account_id=account_id,
                is_active_in_account=True
            )
            return account_user.phone_number
        except AccountUser.DoesNotExist:
            return None
    
    def get_role(self, obj):
        """Get role from AccountUser based on account context"""
        request = self.context.get('request')
        if not request:
            return None
            
        # Get account_id from header
        account_id = request.headers.get('X-Account-Context')
        if not account_id:
            return None
            
        try:
            from platform_accounts.models import AccountUser
            account_user = AccountUser.objects.get(
                user=obj,
                account__account_id=account_id,
                is_active_in_account=True
            )
            return account_user.role
        except AccountUser.DoesNotExist:
            return None
    
    def get_role_display(self, obj):
        """Get role display name from AccountUser based on account context"""
        request = self.context.get('request')
        if not request:
            return None
            
        # Get account_id from header
        account_id = request.headers.get('X-Account-Context')
        if not account_id:
            return None
            
        try:
            from platform_accounts.models import AccountUser
            account_user = AccountUser.objects.get(
                user=obj,
                account__account_id=account_id,
                is_active_in_account=True
            )
            return account_user.get_role_display()
        except AccountUser.DoesNotExist:
            return None
    
    def get_specialty(self, obj):
        """Get specialty from AccountUser based on account context"""
        request = self.context.get('request')
        if not request:
            return None
            
        # Get account_id from header
        account_id = request.headers.get('X-Account-Context')
        if not account_id:
            return None
            
        try:
            from platform_accounts.models import AccountUser
            account_user = AccountUser.objects.get(
                user=obj,
                account__account_id=account_id,
                is_active_in_account=True
            )
            if account_user.specialty:
                return {
                    'id': account_user.specialty.id,
                    'name': account_user.specialty.name
                }
            return None
        except AccountUser.DoesNotExist:
            return None

from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # Add custom claims
        token['email'] = user.email
        token['first_name'] = user.first_name
        token['last_name'] = user.last_name
        token['is_staff'] = user.is_staff
        token['is_superuser'] = user.is_superuser

        return token

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer