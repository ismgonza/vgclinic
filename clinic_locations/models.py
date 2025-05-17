# clinic_locations/models.py
from django.db import models
from django.utils.translation import gettext_lazy as _
from platform_accounts.models import Account

class Location(models.Model):
    """
    Represents a physical location or branch of a clinic.
    """
    account = models.ForeignKey(
        Account, 
        on_delete=models.CASCADE, 
        related_name='locations',
        verbose_name=_('account')
    )
    name = models.CharField(_('name'), max_length=100)
    
    # Contact information
    email = models.EmailField(_('email'), blank=True)
    phone = models.CharField(_('phone number'), max_length=20, blank=True)
    
    # Address
    province = models.CharField(_('province'), max_length=100)
    canton = models.CharField(_('canton'), max_length=100)
    district = models.CharField(_('district'), max_length=100)
    address = models.TextField(_('detailed address'))
    
    # Status and metadata
    is_active = models.BooleanField(_('active'), default=True)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    class Meta:
        verbose_name = _('location')
        verbose_name_plural = _('locations')
        ordering = ['account', 'name']
        unique_together = [['account', 'name']]
    
    def __str__(self):
        return f"{self.name} ({self.account.name})"


class Room(models.Model):
    """
    Represents a room or specific area within a location.
    Used for appointment scheduling and resource allocation.
    """
    location = models.ForeignKey(
        Location, 
        on_delete=models.CASCADE, 
        related_name='rooms',
        verbose_name=_('location')
    )
    name = models.CharField(_('name'), max_length=100)
    
    # Status
    is_active = models.BooleanField(_('active'), default=True)
    is_private = models.BooleanField(_('private'), default=False)
    
    # Metadata
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    class Meta:
        verbose_name = _('room')
        verbose_name_plural = _('rooms')
        ordering = ['location', 'name']
        unique_together = [['location', 'name']]
    
    def __str__(self):
        return f"{self.name} - {self.location.name}"