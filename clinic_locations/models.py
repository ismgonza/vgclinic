# clinic_locations/models.py
from django.db import models
from django.utils.translation import gettext_lazy as _
from platform_accounts.models import Account

class Branch(models.Model):
    """Model representing a clinic branch/location."""
    account = models.ForeignKey(
        Account, 
        on_delete=models.CASCADE, 
        related_name='branches',
        verbose_name=_('account')
    )
    name = models.CharField(_('name'), max_length=255)
    email = models.EmailField(_('email'))
    phone = models.CharField(_('phone number'), max_length=20)
    province = models.CharField(_('province'), max_length=100)
    canton = models.CharField(_('canton'), max_length=100)
    district = models.CharField(_('district'), max_length=100)
    address = models.TextField(_('detailed address'))
    is_active = models.BooleanField(_('active'), default=True)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    class Meta:
        verbose_name = _('location')
        verbose_name_plural = _('locations')
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.account.account_name})"


class Room(models.Model):
    """Model representing a room within a branch."""
    branch = models.ForeignKey(
        Branch, 
        on_delete=models.CASCADE, 
        related_name='rooms',
        verbose_name=_('location')
    )
    name = models.CharField(_('name'), max_length=100)
    is_active = models.BooleanField(_('active'), default=True)
    is_private = models.BooleanField(_('private'), default=False)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    class Meta:
        verbose_name = _('room')
        verbose_name_plural = _('rooms')
        ordering = ['branch', 'name']
    
    def __str__(self):
        return f"{self.name} - {self.branch.name}"