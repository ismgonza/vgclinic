from django.db import models
from django.utils.translation import gettext_lazy as _
from platform_users.models import User

class Account(models.Model):
    """
    An account represents a clinic or organization in the system.
    This is the top-level entity for multi-tenancy.
    """
    STATUS_CHOICES = (
        ('active', _('Active')),
        ('pending', _('Pending')),
        ('suspended', _('Suspended')),
        ('terminated', _('Terminated')),
    )
    
    name = models.CharField(_('name'), max_length=255)
    slug = models.SlugField(_('slug'), max_length=255, unique=True)
    description = models.TextField(_('description'), blank=True)
    logo = models.ImageField(_('logo'), upload_to='account_logos/', blank=True, null=True)
    website = models.URLField(_('website'), blank=True)
    email = models.EmailField(_('contact email'), blank=True)
    phone = models.CharField(_('phone number'), max_length=20, blank=True)
    address = models.TextField(_('address'), blank=True)
    status = models.CharField(_('status'), max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    # Owner represents the main admin for this account (typically someone who signed up)
    owner = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        related_name='owned_accounts', 
        null=True, 
        verbose_name=_('owner')
    )
    
    class Meta:
        verbose_name = _('account')
        verbose_name_plural = _('accounts')
        ordering = ['name']
    
    def __str__(self):
        return self.name


class AccountUser(models.Model):
    """
    Links Users to Accounts with specific roles.
    A User can belong to multiple accounts with different roles.
    """
    ROLE_CHOICES = (
        ('admin', _('Administrator')),
        ('manager', _('Manager')),
        ('staff', _('Staff')),
        ('doctor', _('Doctor')),
        ('assistant', _('Assistant')),
        ('readonly', _('Read-only')),
    )
    
    account = models.ForeignKey(
        Account, 
        on_delete=models.CASCADE, 
        related_name='members', 
        verbose_name=_('account')
    )
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='account_memberships', 
        verbose_name=_('user')
    )
    role = models.CharField(_('role'), max_length=20, choices=ROLE_CHOICES, default='staff')
    is_active = models.BooleanField(_('active'), default=True)
    joined_at = models.DateTimeField(_('joined at'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('account user')
        verbose_name_plural = _('account users')
        unique_together = ('account', 'user')  # A user can have only one role per account
    
    def __str__(self):
        return f"{self.user.email} - {self.account.name} ({self.get_role_display()})"


class AccountInvitation(models.Model):
    """
    Invitations for users to join accounts.
    """
    STATUS_CHOICES = (
        ('pending', _('Pending')),
        ('accepted', _('Accepted')),
        ('declined', _('Declined')),
        ('expired', _('Expired')),
    )
    
    account = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        related_name='invitations',
        verbose_name=_('account')
    )
    email = models.EmailField(_('email address'))
    role = models.CharField(_('role'), max_length=20, choices=AccountUser.ROLE_CHOICES, default='staff')
    invitation_code = models.CharField(_('invitation code'), max_length=64, unique=True)
    status = models.CharField(_('status'), max_length=20, choices=STATUS_CHOICES, default='pending')
    invited_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name='sent_invitations',
        null=True,
        verbose_name=_('invited by')
    )
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    expires_at = models.DateTimeField(_('expires at'))
    
    class Meta:
        verbose_name = _('account invitation')
        verbose_name_plural = _('account invitations')
        
    def __str__(self):
        return f"Invitation for {self.email} to {self.account.name}"