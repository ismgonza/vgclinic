# clinic_catalog/models.py
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator
from platform_accounts.models import Account

class Specialty(models.Model):
    """Model representing a medical specialty offered by the clinic."""
    account = models.ForeignKey(
        Account, 
        on_delete=models.CASCADE, 
        related_name='specialties',
        verbose_name=_('account')
    )
    name = models.CharField(_('name'), max_length=100)
    code = models.CharField(_('code'), max_length=50)
    description = models.TextField(_('description'), blank=True)
    is_active = models.BooleanField(_('active'), default=True)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    class Meta:
        verbose_name = _('specialty')
        verbose_name_plural = _('specialties')
        unique_together = ['account', 'code']  # Code must be unique per account
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name}"


class CatalogItem(models.Model):
    """Model representing a service or product in the clinic's catalog."""
    account = models.ForeignKey(
        Account, 
        on_delete=models.CASCADE, 
        related_name='catalog_items',
        verbose_name=_('account')
    )
    specialty = models.ForeignKey(
        Specialty,
        on_delete=models.CASCADE,
        related_name='catalog_items',
        verbose_name=_('specialty')
    )
    code = models.CharField(_('code'), max_length=50)
    name = models.CharField(_('name'), max_length=255)
    description = models.TextField(_('description'), blank=True)
    price = models.DecimalField(
        _('price'), 
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(0.0)]
    )
    is_variable_price = models.BooleanField(
        _('variable price'), 
        default=False,
        help_text=_('If enabled, the price can be adjusted when creating a procedure')
    )
    is_active = models.BooleanField(_('active'), default=True)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    class Meta:
        verbose_name = _('catalog item')
        verbose_name_plural = _('catalog items')
        unique_together = ['account', 'code']  # Code must be unique per account
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.code})"