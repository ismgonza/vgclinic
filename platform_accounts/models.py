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

class Role(models.Model):
    """Model representing user roles within accounts."""
    ROLE_CHOICES = [
        ('own', _('Owner')),
        ('adm', _('Administrator')),
        ('doc', _('Doctor')),
        ('ast', _('Assistant')),
        ('rdo', _('Read Only')),
    ]
    
    id = models.CharField(
        max_length=3, 
        primary_key=True, 
        choices=ROLE_CHOICES,
        verbose_name=_('Role ID')
    )
    role_name = models.CharField(_('Role Name'), max_length=50)
    role_description = models.TextField(_('Description'))
    
    def __str__(self):
        return self.role_name
    
    class Meta:
        verbose_name = _('Role')
        verbose_name_plural = _('Roles')

class AccountUser(models.Model):
    """Model representing the relationship between users and accounts."""
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
    role = models.ForeignKey(
        Role, 
        on_delete=models.PROTECT,  # Protect to prevent role deletion if users have it
        verbose_name=_('Role')
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
        # Ensure a user can only have one active relationship with an account
        unique_together = ['user', 'account']
        ordering = ['account', 'role', 'user']
    
    def __str__(self):
        return f"{self.user} - {self.account} ({self.role})"