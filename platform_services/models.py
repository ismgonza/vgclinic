# platform_services/models.py
from django.db import models
from django.utils.translation import gettext_lazy as _

class Feature(models.Model):
    """
    A feature represents a specific functionality of the platform.
    Features can be grouped into services and assigned to plans.
    """
    CATEGORY_CHOICES = (
        ('core', _('Core Features')),
        ('patient', _('Patient Management')),
        ('appointment', _('Appointment Scheduling')),
        ('billing', _('Billing and Payments')),
        ('reporting', _('Reporting and Analytics')),
        ('communication', _('Communication')),
        ('integration', _('Integrations')),
        ('advanced', _('Advanced Features')),
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
    
    # For UI display and marketing
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
    A plan defines a set of services and features that are available to accounts.
    Plans can be free or paid, and can have different billing periods.
    """
    BILLING_PERIOD_CHOICES = (
        ('monthly', _('Monthly')),
        ('quarterly', _('Quarterly')),
        ('biannual', _('Bi-Annual')),
        ('annual', _('Annual')),
    )
    
    name = models.CharField(_('name'), max_length=100)
    code = models.SlugField(_('code'), max_length=100, unique=True)
    description = models.TextField(_('description'), blank=True)
    services = models.ManyToManyField(Service, related_name='plans', blank=True)
    features = models.ManyToManyField(Feature, related_name='plans', blank=True,
                                    help_text=_('Additional features not included in the selected services'))
    
    # Pricing information
    is_free = models.BooleanField(_('free plan'), default=False)
    base_price = models.DecimalField(_('base price'), max_digits=10, decimal_places=2, default=0)
    billing_period = models.CharField(_('billing period'), max_length=20, 
                                    choices=BILLING_PERIOD_CHOICES, default='monthly')
    
    # Quotas and limits
    max_users = models.PositiveIntegerField(_('maximum users'), default=5, 
                                          help_text=_('Maximum number of users allowed'))
    max_locations = models.PositiveIntegerField(_('maximum locations'), default=1, 
                                              help_text=_('Maximum number of locations/branches'))
    max_storage_gb = models.PositiveIntegerField(_('maximum storage (GB)'), default=5, 
                                              help_text=_('Maximum storage in gigabytes'))
    
    # Marketing and display
    is_featured = models.BooleanField(_('featured plan'), default=False)
    is_public = models.BooleanField(_('publicly visible'), default=True)
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
        if self.is_free:
            return f"{self.name} (Free)"
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