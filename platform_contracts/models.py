from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from platform_accounts.models import Account
from platform_services.models import Plan
from platform_users.models import User

class ContractStatus(models.Model):
    """
    Represents possible statuses for a contract.
    """
    code = models.CharField(_('code'), max_length=20, primary_key=True)
    name = models.CharField(_('name'), max_length=100)
    description = models.TextField(_('description'), blank=True)
    
    class Meta:
        verbose_name = _('contract status')
        verbose_name_plural = _('contract statuses')
        
    def __str__(self):
        return self.name


class Contract(models.Model):
    """
    A contract links an account or user to a specific plan for a period of time.
    """
    contract_number = models.CharField(_('contract number'), max_length=14, primary_key=True,
                                     help_text=_('Format: YYYYMMDDHHMMSS'))
    plan = models.ForeignKey(
        Plan, 
        on_delete=models.PROTECT, 
        related_name='contracts', 
        verbose_name=_('plan')
    )
    
    # Contract type and target
    CONTRACT_TYPE_CHOICES = (
        ('account', _('Account Contract')),
        ('user', _('User Contract')),
    )
    contract_type = models.CharField(_('contract type'), max_length=10, choices=CONTRACT_TYPE_CHOICES)
    account = models.ForeignKey(
        Account, 
        on_delete=models.CASCADE, 
        related_name='contracts', 
        verbose_name=_('account'),
        null=True,
        blank=True
    )
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='contracts', 
        verbose_name=_('user'),
        null=True,
        blank=True
    )
    
    # Status and dates
    status = models.ForeignKey(
        ContractStatus,
        on_delete=models.PROTECT,
        related_name='contracts',
        verbose_name=_('status')
    )
    is_trial = models.BooleanField(_('is trial'), default=False)
    start_date = models.DateTimeField(_('start date'), default=timezone.now)
    end_date = models.DateTimeField(_('end date'), null=True, blank=True)
    
    # Payment details
    price_override = models.DecimalField(
        _('price override'), 
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text=_('Custom price for this contract (if different from plan price)')
    )
    billing_period = models.CharField(
        _('billing period'), 
        max_length=20, 
        choices=Plan.BILLING_PERIOD_CHOICES, 
        default='monthly'
    )
    auto_renew = models.BooleanField(_('auto renew'), default=True)
    
    # Metadata
    notes = models.TextField(_('notes'), blank=True)
    
    # For internal use
    created_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='created_contracts', 
        verbose_name=_('created by')
    )
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    class Meta:
        verbose_name = _('contract')
        verbose_name_plural = _('contracts')
        ordering = ['-start_date']
    
    def __str__(self):
        if self.contract_type == 'account':
            target = self.account.account_name if self.account else 'Unknown Account'
        else:
            target = str(self.user) if self.user else 'Unknown User'
        return f"{target} - {self.plan.name} ({self.status.name})"
    
    def save(self, *args, **kwargs):
        # Validate that either account or user is set based on contract_type
        if self.contract_type == 'account' and not self.account:
            raise ValueError(_('Account contract must have an account specified'))
        if self.contract_type == 'user' and not self.user:
            raise ValueError(_('User contract must have a user specified'))
        
        # If this is a new contract (no primary key yet), generate contract number
        if not self.contract_number:
            self.contract_number = timezone.now().strftime('%Y%m%d%H%M%S')
            
        super().save(*args, **kwargs)
    
    @property
    def is_active(self):
        """Check if contract is currently active."""
        active_statuses = ['active', 'trial']
        is_status_active = self.status.code in active_statuses
        is_date_valid = True
        
        if self.end_date and self.end_date < timezone.now():
            is_date_valid = False
            
        return is_status_active and is_date_valid


class FeatureOverride(models.Model):
    """
    Allows custom overrides for features on a per-contract basis.
    This can be used to grant or restrict specific features for an account or user,
    regardless of their plan.
    """
    OVERRIDE_TYPE_CHOICES = (
        ('grant', _('Grant Access')),
        ('restrict', _('Restrict Access')),
    )
    
    contract = models.ForeignKey(
        Contract, 
        on_delete=models.CASCADE, 
        related_name='feature_overrides', 
        verbose_name=_('contract')
    )
    feature_code = models.CharField(_('feature code'), max_length=100)
    override_type = models.CharField(_('override type'), max_length=10, choices=OVERRIDE_TYPE_CHOICES)
    reason = models.TextField(_('reason'), blank=True)
    
    # For internal use
    created_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='created_feature_overrides', 
        verbose_name=_('created by')
    )
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    expires_at = models.DateTimeField(_('expires at'), null=True, blank=True)
    
    class Meta:
        verbose_name = _('feature override')
        verbose_name_plural = _('feature overrides')
        unique_together = ('contract', 'feature_code')
    
    def __str__(self):
        return f"{self.contract} - {self.feature_code} ({self.get_override_type_display()})"


class UsageQuota(models.Model):
    """
    Tracks the usage of resources for an account or user against their plan limits.
    """
    QUOTA_TYPE_CHOICES = (
        ('users', _('Users')),
        ('locations', _('Locations')),
        ('api_calls', _('API Calls')),
        ('sms', _('SMS Messages')),
        ('email', _('Email Messages')),
    )
    
    contract = models.ForeignKey(
        Contract, 
        on_delete=models.CASCADE, 
        related_name='quotas', 
        verbose_name=_('contract')
    )
    quota_type = models.CharField(_('quota type'), max_length=20, choices=QUOTA_TYPE_CHOICES)
    limit = models.PositiveIntegerField(_('limit'))
    current_usage = models.PositiveIntegerField(_('current usage'), default=0)
    
    # For internal use
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    class Meta:
        verbose_name = _('usage quota')
        verbose_name_plural = _('usage quotas')
        unique_together = ('contract', 'quota_type')
    
    def __str__(self):
        return f"{self.contract} - {self.get_quota_type_display()}: {self.current_usage}/{self.limit}"
    
    @property
    def percentage_used(self):
        """Calculate the percentage of quota used."""
        if self.limit == 0:  # Avoid division by zero
            return 100 if self.current_usage > 0 else 0
        return (self.current_usage * 100) / self.limit
    
    @property
    def is_exceeded(self):
        """Check if quota is exceeded."""
        return self.current_usage > self.limit