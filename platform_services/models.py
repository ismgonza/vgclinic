from django.db import models
from django.utils.translation import gettext_lazy as _

class Feature(models.Model):
    """
    A feature represents a specific functionality of the platform.
    Features can be grouped into services and assigned to plans.
    """
    CATEGORY_CHOICES = (
        ('core', _('Core Features')),
        ('analytics', _('Analytics and Reporting')),
        ('billing', _('Billing and Payments')),
        ('appointments', _('Appointments and Scheduling')),
        ('communications', _('Communications')),
    )
    
    name = models.CharField(_('name'), max_length=100)
    code = models.SlugField(_('code'), max_length=100, unique=True, 
                          help_text=_('Unique identifier used in permission checks'))
    description = models.TextField(_('description'), blank=True)
    category = models.CharField(_('category'), max_length=20, choices=CATEGORY_CHOICES)
    is_active = models.BooleanField(_('active'), default=True)
    
    # For UI display and organization
    icon = models.CharField(_('icon'), max_length=50, blank=True)
    ui_order = models.PositiveIntegerField(_('UI display order'), default=0)
    
    # For internal use
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    class Meta:
        verbose_name = _('feature')
        verbose_name_plural = _('features')
        ordering = ['category', 'ui_order', 'name']
    
    def __str__(self):
        return self.name


class Service(models.Model):
    """
    A service is a collection of related features.
    Services can be included in different plans.
    """
    name = models.CharField(_('name'), max_length=100)
    code = models.SlugField(_('code'), max_length=100, unique=True)
    description = models.TextField(_('description'), blank=True)
    features = models.ManyToManyField(Feature, related_name='services', blank=True)
    is_active = models.BooleanField(_('active'), default=True)
    
    # For UI display and organization
    icon = models.CharField(_('icon'), max_length=50, blank=True)
    ui_order = models.PositiveIntegerField(_('UI display order'), default=0)
    
    # For internal use
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    class Meta:
        verbose_name = _('service')
        verbose_name_plural = _('services')
        ordering = ['ui_order', 'name']
    
    def __str__(self):
        return self.name


class Plan(models.Model):
    """
    A plan defines a set of services and features that are available.
    Plans can be for accounts or individual users.
    """
    BILLING_PERIOD_CHOICES = (
        ('monthly', _('Monthly')),
        ('quarterly', _('Quarterly')),
        ('biannual', _('Bi-Annual')),
        ('annual', _('Annual')),
    )
    
    PLAN_TYPE_CHOICES = (
        ('account', _('Account Plan')),
        ('user', _('User Plan')),
    )
    
    name = models.CharField(_('name'), max_length=100)
    code = models.SlugField(_('code'), max_length=100, unique=True)
    description = models.TextField(_('description'), blank=True)
    plan_type = models.CharField(_('plan type'), max_length=10, choices=PLAN_TYPE_CHOICES)
    services = models.ManyToManyField(Service, related_name='plans', blank=True)
    features = models.ManyToManyField(Feature, related_name='plans', blank=True,
                                    help_text=_('Additional features not included in the selected services'))
    
    # Pricing information
    base_price = models.DecimalField(_('base price'), max_digits=10, decimal_places=2, default=0)
    billing_period = models.CharField(_('billing period'), max_length=20, 
                                    choices=BILLING_PERIOD_CHOICES, default='monthly')
    
    # Quotas and limits
    max_users = models.PositiveIntegerField(_('maximum users'), default=5, 
                                          help_text=_('Maximum number of users allowed'))
    max_locations = models.PositiveIntegerField(_('maximum locations'), default=1, 
                                              help_text=_('Maximum number of locations/branches'))
    
    # For display
    ui_order = models.PositiveIntegerField(_('UI display order'), default=0)
    
    # For internal use
    is_active = models.BooleanField(_('active'), default=True)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    class Meta:
        verbose_name = _('plan')
        verbose_name_plural = _('plans')
        ordering = ['ui_order', 'base_price', 'name']
    
    def __str__(self):
        return f"{self.name} (${self.base_price}/{self.get_billing_period_display()})"
    
    @property
    def all_features(self):
        """
        Returns a QuerySet of all features included in this plan,
        either directly or through services.
        """
        direct_features = self.features.all()
        service_features = Feature.objects.filter(services__in=self.services.all())
        return (direct_features | service_features).distinct()