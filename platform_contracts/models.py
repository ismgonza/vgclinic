# platform_contracts/models.py
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from platform_accounts.models import Account
from platform_services.models import Plan
from platform_users.models import User

class Subscription(models.Model):
    """
    A subscription links an account to a specific plan for a period of time.
    It tracks billing status, renewal dates, and payment information.
    """
    STATUS_CHOICES = (
        ('active', _('Active')),
        ('trialing', _('Trial')),
        ('past_due', _('Past Due')),
        ('canceled', _('Canceled')),
        ('expired', _('Expired')),
    )
    
    account = models.ForeignKey(
        Account, 
        on_delete=models.CASCADE, 
        related_name='subscriptions', 
        verbose_name=_('account')
    )
    plan = models.ForeignKey(
        Plan, 
        on_delete=models.PROTECT, 
        related_name='subscriptions', 
        verbose_name=_('plan')
    )
    status = models.CharField(_('status'), max_length=20, choices=STATUS_CHOICES, default='active')
    
    # Subscription dates
    start_date = models.DateTimeField(_('start date'), default=timezone.now)
    end_date = models.DateTimeField(_('end date'), null=True, blank=True)
    trial_end = models.DateTimeField(_('trial end'), null=True, blank=True)
    canceled_at = models.DateTimeField(_('canceled at'), null=True, blank=True)
    
    # Payment details (can be expanded based on your payment provider)
    is_paid = models.BooleanField(_('is paid'), default=False)
    next_billing_date = models.DateTimeField(_('next billing date'), null=True, blank=True)
    billing_period = models.CharField(_('billing period'), max_length=20, 
                                    choices=Plan.BILLING_PERIOD_CHOICES, default='monthly')
    price_override = models.DecimalField(_('price override'), max_digits=10, decimal_places=2, 
                                       null=True, blank=True,
                                       help_text=_('Custom price for this subscription (if different from plan price)'))
    
    # Metadata
    auto_renew = models.BooleanField(_('auto renew'), default=True)
    cancellation_reason = models.TextField(_('cancellation reason'), blank=True)
    notes = models.TextField(_('notes'), blank=True)
    
    # External IDs for payment processors
    payment_provider = models.CharField(_('payment provider'), max_length=50, blank=True)
    external_id = models.CharField(_('external ID'), max_length=100, blank=True, 
                                 help_text=_('ID used by the payment provider'))
    
    # For internal use
    created_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='created_subscriptions', 
        verbose_name=_('created by')
    )
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    class Meta:
        verbose_name = _('subscription')
        verbose_name_plural = _('subscriptions')
        ordering = ['-start_date']
    
    def __str__(self):
        return f"{self.account.name} - {self.plan.name} ({self.get_status_display()})"
    
    @property
    def is_active(self):
        """Check if subscription is currently active."""
        if self.status in ['active', 'trialing']:
            if self.end_date and self.end_date < timezone.now():
                return False
            return True
        return False
    
    def cancel(self, reason=''):
        """Cancel the subscription."""
        self.status = 'canceled'
        self.canceled_at = timezone.now()
        self.auto_renew = False
        self.cancellation_reason = reason
        self.save()


class FeatureOverride(models.Model):
    """
    Allows custom overrides for features on a per-subscription basis.
    This can be used to grant or restrict specific features for an account,
    regardless of their plan.
    """
    OVERRIDE_TYPE_CHOICES = (
        ('grant', _('Grant Access')),
        ('restrict', _('Restrict Access')),
    )
    
    subscription = models.ForeignKey(
        Subscription, 
        on_delete=models.CASCADE, 
        related_name='feature_overrides', 
        verbose_name=_('subscription')
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
        unique_together = ('subscription', 'feature_code')
    
    def __str__(self):
        return f"{self.subscription.account.name} - {self.feature_code} ({self.get_override_type_display()})"


class UsageQuota(models.Model):
    """
    Tracks the usage of resources for an account against their plan limits.
    """
    QUOTA_TYPE_CHOICES = (
        ('users', _('Users')),
        ('locations', _('Locations')),
        ('storage', _('Storage (GB)')),
        ('api_calls', _('API Calls')),
        ('sms', _('SMS Messages')),
        ('email', _('Email Messages')),
    )
    
    subscription = models.ForeignKey(
        Subscription, 
        on_delete=models.CASCADE, 
        related_name='quotas', 
        verbose_name=_('subscription')
    )
    quota_type = models.CharField(_('quota type'), max_length=20, choices=QUOTA_TYPE_CHOICES)
    limit = models.PositiveIntegerField(_('limit'))
    current_usage = models.PositiveIntegerField(_('current usage'), default=0)
    
    # For internal use
    reset_date = models.DateTimeField(_('last reset date'), auto_now_add=True)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    class Meta:
        verbose_name = _('usage quota')
        verbose_name_plural = _('usage quotas')
        unique_together = ('subscription', 'quota_type')
    
    def __str__(self):
        return f"{self.subscription.account.name} - {self.get_quota_type_display()}: {self.current_usage}/{self.limit}"
    
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


class Invoice(models.Model):
    """
    Represents an invoice generated for a subscription.
    """
    STATUS_CHOICES = (
        ('draft', _('Draft')),
        ('pending', _('Pending')),
        ('paid', _('Paid')),
        ('overdue', _('Overdue')),
        ('canceled', _('Canceled')),
    )
    
    subscription = models.ForeignKey(
        Subscription, 
        on_delete=models.CASCADE, 
        related_name='invoices', 
        verbose_name=_('subscription')
    )
    invoice_number = models.CharField(_('invoice number'), max_length=50, unique=True)
    status = models.CharField(_('status'), max_length=20, choices=STATUS_CHOICES, default='draft')
    
    amount = models.DecimalField(_('amount'), max_digits=10, decimal_places=2)
    tax_amount = models.DecimalField(_('tax amount'), max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(_('total amount'), max_digits=10, decimal_places=2)
    
    # Dates
    issue_date = models.DateField(_('issue date'), default=timezone.now)
    due_date = models.DateField(_('due date'))
    paid_date = models.DateField(_('paid date'), null=True, blank=True)
    
    # External payment info
    payment_method = models.CharField(_('payment method'), max_length=50, blank=True)
    payment_reference = models.CharField(_('payment reference'), max_length=100, blank=True)
    
    # For internal use
    notes = models.TextField(_('notes'), blank=True)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    class Meta:
        verbose_name = _('invoice')
        verbose_name_plural = _('invoices')
        ordering = ['-issue_date', '-id']
    
    def __str__(self):
        return f"Invoice #{self.invoice_number} - {self.subscription.account.name}"


class InvoiceItem(models.Model):
    """
    Represents a line item on an invoice.
    """
    invoice = models.ForeignKey(
        Invoice, 
        on_delete=models.CASCADE, 
        related_name='items', 
        verbose_name=_('invoice')
    )
    description = models.CharField(_('description'), max_length=255)
    quantity = models.PositiveIntegerField(_('quantity'), default=1)
    unit_price = models.DecimalField(_('unit price'), max_digits=10, decimal_places=2)
    amount = models.DecimalField(_('amount'), max_digits=10, decimal_places=2)
    
    class Meta:
        verbose_name = _('invoice item')
        verbose_name_plural = _('invoice items')
    
    def __str__(self):
        return f"{self.description} ({self.quantity} x ${self.unit_price})"