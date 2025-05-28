# platform_accounts/serializers.py
from rest_framework import serializers
from .models import Account, AccountOwner, AccountUser, AccountInvitation, AccountAuthorization
from platform_users.serializers import UserSerializer

class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = ('account_id', 'account_name', 'account_logo', 'account_website',
                  'account_email', 'account_phone', 'account_address',
                  'account_status', 'is_platform_account', 'account_created_at')
        read_only_fields = ('account_id', 'account_created_at')

class AccountOwnerSerializer(serializers.ModelSerializer):
    user_details = UserSerializer(source='user', read_only=True)
    account_details = AccountSerializer(source='account', read_only=True)
    
    class Meta:
        model = AccountOwner
        fields = ('id', 'user', 'account', 'is_active', 'created_at', 
                  'user_details', 'account_details')
        read_only_fields = ('id', 'created_at')

class AccountUserSerializer(serializers.ModelSerializer):
    user_details = UserSerializer(source='user', read_only=True)
    account_details = AccountSerializer(source='account', read_only=True)
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    specialty_details = serializers.SerializerMethodField()
    
    class Meta:
        model = AccountUser
        fields = ('id', 'user', 'account', 'role', 'role_display', 'specialty', 
                  'specialty_details', 'color', 'phone_number', 'is_active_in_account', 
                  'created_at', 'user_details', 'account_details')
        read_only_fields = ('id', 'created_at')
    
    def get_specialty_details(self, obj):
        if obj.specialty:
            from clinic_catalog.serializers import SpecialtySerializer
            return SpecialtySerializer(obj.specialty).data
        return None
    
class AccountInvitationSerializer(serializers.ModelSerializer):
    invited_by_details = UserSerializer(source='invited_by', read_only=True)
    account_details = AccountSerializer(source='account', read_only=True)
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    specialty_details = serializers.SerializerMethodField()
    is_valid = serializers.BooleanField(read_only=True)
    is_expired = serializers.BooleanField(read_only=True)
    acceptance_url = serializers.SerializerMethodField()
    
    class Meta:
        model = AccountInvitation
        fields = ('id', 'email', 'account', 'role', 'role_display', 'specialty', 
                  'specialty_details', 'status', 'status_display', 'personal_message', 
                  'notes', 'created_at', 'expires_at', 'accepted_at', 'invited_by',
                  'invited_by_details', 'account_details', 'is_valid', 'is_expired',
                  'acceptance_url', 'token')
        read_only_fields = ('id', 'token', 'created_at', 'accepted_at', 'invited_by')
    
    def get_specialty_details(self, obj):
        if obj.specialty:
            from clinic_catalog.serializers import SpecialtySerializer
            return SpecialtySerializer(obj.specialty).data
        return None
    
    def get_acceptance_url(self, obj):
        request = self.context.get('request')
        return obj.get_acceptance_url(request)

class CreateInvitationSerializer(serializers.ModelSerializer):
    """Simplified serializer for creating invitations."""
    
    class Meta:
        model = AccountInvitation
        fields = ('email', 'account', 'role', 'specialty', 'personal_message', 'notes')
    
    def validate_email(self, value):
        """Validate email format and check for existing users."""
        # Basic email validation is handled by EmailField
        return value.lower()
    
    def validate(self, data):
        """Validate the invitation data."""
        account = data.get('account')
        email = data.get('email')
        role = data.get('role')
        
        # Check if there's already a pending invitation for this email/account
        existing_invitation = AccountInvitation.objects.filter(
            email=email,
            account=account,
            status='pending'
        ).first()
        
        if existing_invitation and existing_invitation.is_valid():
            raise serializers.ValidationError(
                f"A pending invitation already exists for {email} to join {account.account_name}"
            )
        
        # Check if user is already a member of this account
        from platform_users.models import User
        try:
            existing_user = User.objects.get(email=email)
            if AccountUser.objects.filter(user=existing_user, account=account, is_active_in_account=True).exists():
                raise serializers.ValidationError(
                    f"User {email} is already a member of {account.account_name}"
                )
        except User.DoesNotExist:
            # User doesn't exist yet, which is fine for invitations
            pass
        
        # If role is doctor, specialty should be recommended but not required
        if role == 'doc' and not data.get('specialty'):
            # Just a warning, not an error
            pass
        
        return data

class AcceptInvitationSerializer(serializers.Serializer):
    """Serializer for accepting invitations."""
    token = serializers.CharField(max_length=64)
    
    # Fields for new user creation (only if user doesn't exist)
    first_name = serializers.CharField(max_length=30, required=False)
    last_name = serializers.CharField(max_length=30, required=False) 
    id_type = serializers.ChoiceField(choices=[('01', 'Cédula'), ('02', 'DIMEX')], required=False)
    id_number = serializers.CharField(max_length=12, required=False)
    password = serializers.CharField(write_only=True, required=False)
    confirm_password = serializers.CharField(write_only=True, required=False)
    
    def validate_token(self, value):
        """Validate that the token exists and is valid."""
        try:
            invitation = AccountInvitation.objects.get(token=value)
            if not invitation.is_valid():
                if invitation.is_expired():
                    raise serializers.ValidationError("This invitation has expired.")
                else:
                    raise serializers.ValidationError("This invitation is no longer valid.")
            return value
        except AccountInvitation.DoesNotExist:
            raise serializers.ValidationError("Invalid invitation token.")
    
    def validate(self, data):
        """Validate the acceptance data."""
        token = data.get('token')
        invitation = AccountInvitation.objects.get(token=token)
        
        # Check if user already exists
        from platform_users.models import User
        try:
            existing_user = User.objects.get(email=invitation.email)
            # User exists, no need for additional fields
            data['existing_user'] = existing_user
        except User.DoesNotExist:
            # User doesn't exist, validate required fields for creation
            required_fields = ['first_name', 'last_name', 'id_type', 'id_number', 'password', 'confirm_password']
            for field in required_fields:
                if not data.get(field):
                    raise serializers.ValidationError(f"{field} is required for new user creation.")
            
            # Validate password confirmation
            if data['password'] != data['confirm_password']:
                raise serializers.ValidationError("Passwords do not match.")
            
            # Validate password strength (basic)
            if len(data['password']) < 8:
                raise serializers.ValidationError("Password must be at least 8 characters long.")
        
        data['invitation'] = invitation
        return data
    
class AccountAuthorizationSerializer(serializers.ModelSerializer):
    """Serializer for individual account authorizations."""
    user_details = UserSerializer(source='user', read_only=True)
    granted_by_details = UserSerializer(source='granted_by', read_only=True)
    authorization_display = serializers.CharField(source='get_authorization_type_display', read_only=True)
    is_valid = serializers.SerializerMethodField()
    
    class Meta:
        model = AccountAuthorization
        fields = ('id', 'user', 'account', 'authorization_type', 'authorization_display',
                  'granted_by', 'is_active', 'granted_at', 'expires_at', 'notes',
                  'user_details', 'granted_by_details', 'is_valid')
        read_only_fields = ('id', 'granted_at', 'granted_by')
    
    def get_is_valid(self, obj):
        return obj.is_valid()

class UserPermissionsSerializer(serializers.Serializer):
    """Serializer for managing a user's permissions within an account."""
    user_id = serializers.IntegerField()
    account_id = serializers.UUIDField()
    permissions = serializers.ListField(
        child=serializers.CharField(max_length=50),
        help_text="List of authorization_type values to grant to the user"
    )
    notes = serializers.CharField(max_length=500, required=False, allow_blank=True)
    
    def validate_user_id(self, value):
        """Validate that the user exists."""
        from platform_users.models import User
        try:
            User.objects.get(id=value)
            return value
        except User.DoesNotExist:
            raise serializers.ValidationError("User does not exist.")
    
    def validate_account_id(self, value):
        """Validate that the account exists."""
        try:
            Account.objects.get(account_id=value)
            return value
        except Account.DoesNotExist:
            raise serializers.ValidationError("Account does not exist.")
    
    def validate_permissions(self, value):
        """Validate that all permissions are valid authorization types."""
        # FIXED: Import from centralized registry
        from .permissions import get_all_permissions
        valid_permissions = [choice[0] for choice in get_all_permissions()]
        invalid_permissions = [p for p in value if p not in valid_permissions]
        
        if invalid_permissions:
            raise serializers.ValidationError(
                f"Invalid permissions: {', '.join(invalid_permissions)}. "
                f"Valid options are: {', '.join(valid_permissions)}"
            )
        
        return value

class UserPermissionsSummarySerializer(serializers.Serializer):
    """Serializer for getting a summary of user permissions."""
    user_id = serializers.IntegerField(read_only=True)
    user_details = UserSerializer(read_only=True)
    role = serializers.CharField(read_only=True)
    role_display = serializers.CharField(read_only=True)
    is_owner = serializers.BooleanField(read_only=True)
    permissions = serializers.ListField(
        child=serializers.CharField(),
        read_only=True,
        help_text="List of authorization types this user has"
    )
    permission_details = AccountAuthorizationSerializer(many=True, read_only=True)