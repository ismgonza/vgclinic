import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _
from platform_users.models import User

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
    ROLE_CHOICES = [
        ('adm', _('Administrator')),
        ('doc', _('Doctor')),
        ('ast', _('Assistant')),
        ('rdo', _('Read Only')),
    ]
    
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
        # Allow multiple roles per user per account - NO unique constraint
        ordering = ['account', 'role', 'user']
    
    def __str__(self):
        return f"{self.user} - {self.account} ({self.get_role_display()})"