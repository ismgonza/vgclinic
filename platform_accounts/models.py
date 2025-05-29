# platform_accounts/models.py - Updated to use centralized roles

import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _
from platform_users.models import User
from .roles import AccountRoles  # Import centralized roles

import secrets
from datetime import timedelta
from django.utils import timezone

class Account(models.Model):
    """Model representing a clinic account."""
    ACCOUNT_STATUS_CHOICES = [
        ('active', _('Active')),
        ('pending', _('Pending')),
        ('suspended', _('Suspended')),
    ]
    
    # Use a UUID for the account_id to prevent enumeration attacks
    account_id = models.UUIDField(
        primary_key=True, 
        default=uuid.uuid4, 
        editable=False,
        verbose_name=_('Account ID')
    )
    account_name = models.CharField(_('Account Name'), max_length=255)
    account_logo = models.ImageField(
        _('Account Logo'), 
        upload_to='account_logos/', 
        null=True, 
        blank=True
    )
    account_website = models.URLField(_('Website'), max_length=255, null=True, blank=True)
    account_email = models.EmailField(_('Email'), max_length=255)
    account_phone = models.CharField(_('Phone'), max_length=20)
    account_address = models.TextField(_('Address'))
    account_status = models.CharField(
        _('Status'),
        max_length=10,
        choices=ACCOUNT_STATUS_CHOICES,
        default='pending'
    )
    is_platform_account = models.BooleanField(
        _('Is Platform Account'),
        default=True,
        help_text=_('Indicates if this is a full platform account or just an external reference')
    )
    account_created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    
    default_language = models.CharField(
        _('Default Language'),
        max_length=5,
        choices=[
            ('en', _('English')),
            ('es', _('Spanish')),
        ],
        default='es',  # Spanish by default since most clinics will use Spanish
        help_text=_('Default language for emails and communications from this account')
    )
    
    def __str__(self):
        return self.account_name
    
    class Meta:
        verbose_name = _('Account')
        verbose_name_plural = _('Accounts')
        ordering = ['account_name']

class AccountOwner(models.Model):
    """Model representing account ownership - separate from operational roles."""
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='owned_accounts',
        verbose_name=_('User')
    )
    account = models.ForeignKey(
        Account, 
        on_delete=models.CASCADE, 
        related_name='owners',
        verbose_name=_('Account')
    )
    is_active = models.BooleanField(
        _('Active Owner'), 
        default=True,
        help_text=_('Indicates if this ownership is currently active')
    )
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('Account Owner')
        verbose_name_plural = _('Account Owners')
        unique_together = ['user', 'account']  # A user can only be owner once per account
        ordering = ['account', 'user']
    
    def __str__(self):
        return f"{self.user} - Owner of {self.account}"

class AccountUser(models.Model):
    """Model representing operational roles of users within accounts."""
    
    # Use centralized role choices
    ROLE_CHOICES = AccountRoles.ROLE_CHOICES

    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='account_memberships',
        verbose_name=_('User')
    )
    account = models.ForeignKey(
        Account, 
        on_delete=models.CASCADE, 
        related_name='members',
        verbose_name=_('Account')
    )
    role = models.CharField(
        _('Role'),
        max_length=3,
        choices=ROLE_CHOICES
    )
    specialty = models.ForeignKey(
        'clinic_catalog.Specialty',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='account_users',
        verbose_name=_('Specialty'),
        help_text=_('Specialty this user practices in this account (required for doctors)')
    )
    color = models.CharField(
        _('Color'), 
        max_length=7, 
        default="#000000",
        help_text=_('Color code for calendar representation (e.g., #FF5733)')
    )
    phone_number = models.CharField(
        _('Phone Number'), 
        max_length=20, 
        null=True, 
        blank=True,
        help_text=_('Contact phone number specific to this account')
    )
    is_active_in_account = models.BooleanField(
        _('Active in Account'), 
        default=True,
        help_text=_('Indicates if the user is active in this specific account')
    )
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('Account User')
        verbose_name_plural = _('Account Users')
        ordering = ['account', 'role', 'user']
    
    def __str__(self):
        return f"{self.user} - {self.account} ({self.get_role_display()})"
    
    def get_role_color(self):
        """Get the color associated with this user's role"""
        return AccountRoles.get_role_color(self.role)
    
    # SIMPLIFIED - Only ONE permission checking method
    @classmethod
    def user_has_permission(cls, user, account, permission_type):
        """
        Unified permission check that considers:
        1. Account ownership (owners have all permissions)
        2. Role-based default permissions  
        3. Individual permission overrides
        """
        # Check if user is an owner (owners have all permissions)
        if AccountOwner.objects.filter(
            user=user, 
            account=account, 
            is_active=True
        ).exists():
            return True
        
        # Check if user is even a member of this account
        try:
            account_user = cls.objects.get(
                user=user,
                account=account,
                is_active_in_account=True
            )
        except cls.DoesNotExist:
            return False
        
        # Check individual permissions first (these override role defaults)
        from django.utils import timezone
        from django.db import models as django_models
        
        if AccountAuthorization.objects.filter(
            user=user,
            account=account,
            authorization_type=permission_type,
            is_active=True
        ).filter(
            django_models.Q(expires_at__isnull=True) | 
            django_models.Q(expires_at__gt=timezone.now())
        ).exists():
            return True
        
        # Check role-based default permissions
        return RolePermission.objects.filter(
            role=account_user.role,
            permission_type=permission_type,
            is_active=True
        ).exists()
    
    # Instance method for convenience
    def has_permission(self, permission_type):
        """Check if this user has a specific permission in this account."""
        return self.user_has_permission(self.user, self.account, permission_type)

class AccountAuthorization(models.Model):
    """
    Model representing specific authorizations granted to users within accounts.
    This allows account owners to grant granular permissions beyond basic roles.
    """
    
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='account_authorizations',
        verbose_name=_('User')
    )
    account = models.ForeignKey(
        Account, 
        on_delete=models.CASCADE, 
        related_name='user_authorizations',
        verbose_name=_('Account')
    )
    authorization_type = models.CharField(
        _('Authorization Type'),
        max_length=50,
        # Note: choices will be handled dynamically in forms/admin
    )
    granted_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='granted_authorizations',
        verbose_name=_('Granted By'),
        help_text=_('The user who granted this authorization')
    )
    is_active = models.BooleanField(
        _('Active'), 
        default=True,
        help_text=_('Whether this authorization is currently active')
    )
    granted_at = models.DateTimeField(_('Granted At'), auto_now_add=True)
    expires_at = models.DateTimeField(
        _('Expires At'), 
        null=True, 
        blank=True,
        help_text=_('Leave blank for permanent authorization')
    )
    notes = models.TextField(
        _('Notes'), 
        blank=True,
        help_text=_('Optional notes about this authorization')
    )
    
    class Meta:
        verbose_name = _('Account Authorization')
        verbose_name_plural = _('Account Authorizations')
        unique_together = ['user', 'account', 'authorization_type']
        ordering = ['account', 'authorization_type', 'user']
    
    def __str__(self):
        return f"{self.user} - {self.account} ({self.authorization_type})"
    
    def is_expired(self):
        """Check if this authorization has expired."""
        if self.expires_at is None:
            return False
        return timezone.now() > self.expires_at
    
    def is_valid(self):
        """Check if this authorization is currently valid."""
        return self.is_active and not self.is_expired()

class RolePermission(models.Model):
    """
    Default permissions assigned to each role.
    This defines what permissions each role gets by default.
    """
    # Use centralized role choices
    ROLE_CHOICES = AccountRoles.ROLE_CHOICES
    
    @staticmethod
    def get_permission_choices():
        from .permissions import get_all_permissions
        return get_all_permissions()
    
    id = models.BigAutoField(primary_key=True)
    role = models.CharField(
        _('Role'),
        max_length=3,
        choices=ROLE_CHOICES
    )
    permission_type = models.CharField(
        _('Permission Type'),
        max_length=50,
        # Note: choices will be handled dynamically in forms/admin
    )
    is_active = models.BooleanField(
        _('Active'), 
        default=True,
        help_text=_('Whether this role permission is currently active')
    )
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('Role Permission')
        verbose_name_plural = _('Role Permissions')
        unique_together = ['role', 'permission_type']
        ordering = ['role', 'permission_type']
    
    def __str__(self):
        return f"{self.get_role_display()} - {self.permission_type}"
    
class AccountInvitation(models.Model):
    """
    Model representing invitations sent to users to join an account.
    Handles both existing users and new user creation.
    """
    
    INVITATION_STATUS_CHOICES = [
        ('pending', _('Pending')),
        ('accepted', _('Accepted')),
        ('expired', _('Expired')),
        ('revoked', _('Revoked')),
    ]
    
    id = models.BigAutoField(primary_key=True)
    
    # Core invitation details
    email = models.EmailField(
        _('Email Address'),
        help_text=_('Email address of the person being invited')
    )
    account = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        related_name='invitations',
        verbose_name=_('Account')
    )
    role = models.CharField(
        _('Role'),
        max_length=3,
        choices=AccountRoles.ROLE_CHOICES,  # Use centralized choices
        help_text=_('Role to assign when invitation is accepted')
    )
    specialty = models.ForeignKey(
        'clinic_catalog.Specialty',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='invitations',
        verbose_name=_('Specialty'),
        help_text=_('Specialty to assign (optional, typically for doctors)')
    )
    
    # Invitation management
    invited_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sent_invitations',
        verbose_name=_('Invited By'),
        help_text=_('User who sent this invitation')
    )
    status = models.CharField(
        _('Status'),
        max_length=10,
        choices=INVITATION_STATUS_CHOICES,
        default='pending'
    )
    
    # Security and tracking
    token = models.CharField(
        _('Token'),
        max_length=64,
        unique=True,
        help_text=_('Secure token for invitation acceptance')
    )
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    expires_at = models.DateTimeField(
        _('Expires At'),
        help_text=_('When this invitation expires')
    )
    accepted_at = models.DateTimeField(
        _('Accepted At'), 
        null=True, 
        blank=True
    )
    accepted_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='accepted_invitations',
        verbose_name=_('Accepted By'),
        help_text=_('User who accepted this invitation (for tracking)')
    )
    
    # Optional fields
    personal_message = models.TextField(
        _('Personal Message'),
        blank=True,
        help_text=_('Optional personal message to include in invitation email')
    )
    notes = models.TextField(
        _('Notes'),
        blank=True,
        help_text=_('Internal notes about this invitation')
    )
    
    class Meta:
        verbose_name = _('Account Invitation')
        verbose_name_plural = _('Account Invitations')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Invitation to {self.email} for {self.account} ({self.get_status_display()})"
    
    def get_role_color(self):
        """Get the color associated with this invitation's role"""
        return AccountRoles.get_role_color(self.role)
    
    def save(self, *args, **kwargs):
        # Generate secure token if not set
        if not self.token:
            self.token = self.generate_secure_token()
        
        # Set expiration if not set (7 days from now)
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(days=7)
        
        super().save(*args, **kwargs)
    
    @staticmethod
    def generate_secure_token():
        """Generate a cryptographically secure token."""
        return secrets.token_urlsafe(48)  # 48 bytes = 64 characters when base64 encoded
    
    def is_expired(self):
        """Check if this invitation has expired."""
        return timezone.now() > self.expires_at
    
    def is_valid(self):
        """Check if this invitation is valid for acceptance."""
        return (
            self.status == 'pending' and 
            not self.is_expired()
        )
    
    def can_be_accepted_by(self, user_email):
        """Check if this invitation can be accepted by the given email."""
        return (
            self.is_valid() and 
            self.email.lower() == user_email.lower()
        )
    
    def mark_as_accepted(self, user):
        """Mark this invitation as accepted by the given user."""
        self.status = 'accepted'
        self.accepted_at = timezone.now()
        self.accepted_by = user
        self.save(update_fields=['status', 'accepted_at', 'accepted_by'])
    
    def mark_as_expired(self):
        """Mark this invitation as expired."""
        self.status = 'expired'
        self.save(update_fields=['status'])
    
    def mark_as_revoked(self):
        """Mark this invitation as revoked."""
        self.status = 'revoked'
        self.save(update_fields=['status'])
    
    def get_acceptance_url(self, request=None):
        """Generate the URL for accepting this invitation."""
        from django.conf import settings
        
        # Try to get frontend URL from settings
        if hasattr(settings, 'FRONTEND_URL'):
            base_url = settings.FRONTEND_URL
        elif request:
            # Build URL from request if available
            protocol = 'https' if request.is_secure() else 'http'
            host = request.get_host()
            base_url = f"{protocol}://{host}"
        else:
            # Fallback for development
            base_url = 'http://localhost:5173'
            
        return f"{base_url}/accept-invitation/{self.token}"