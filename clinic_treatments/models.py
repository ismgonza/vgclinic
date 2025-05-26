# clinic_treatments/models.py
from django.db import models
from django.utils import timezone
from django.conf import settings
from django.utils.translation import gettext_lazy as _


class Treatment(models.Model):
    """
    Base treatment model for all specialties
    """
    
    STATUS_CHOICES = [
        ('SCHEDULED', _('Scheduled')),
        ('RESCHEDULED', _('Rescheduled')),
        ('IN_PROGRESS', _('In Progress')),
        ('COMPLETED', _('Completed')),
        ('CANCELED', _('Canceled')),
    ]
    
    # Relationship to catalog and specialty
    catalog_item = models.ForeignKey('clinic_catalog.CatalogItem', on_delete=models.PROTECT, verbose_name=_('catalog item'))
    specialty = models.ForeignKey('clinic_catalog.Specialty', on_delete=models.PROTECT, verbose_name=_('specialty'))
    
    # Basic information
    patient = models.ForeignKey('clinic_patients.Patient', on_delete=models.CASCADE, related_name='treatments', verbose_name=_('patient'))
    notes = models.TextField(_('notes'), blank=True, help_text=_("Clinical notes, observations, and details specific to this treatment"))
    
    # Scheduling information
    scheduled_date = models.DateTimeField(_('scheduled date'), default=timezone.now)
    completed_date = models.DateTimeField(_('completed date'), null=True, blank=True)
    
    # Status tracking
    status = models.CharField(_('status'), max_length=15, choices=STATUS_CHOICES, default='SCHEDULED')
    
    # Medical details
    doctor = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.PROTECT, 
        related_name='performed_treatments',
        verbose_name=_('doctor')
    )
    location = models.ForeignKey(
        'clinic_locations.Branch', 
        on_delete=models.PROTECT, 
        null=True, 
        blank=True,
        verbose_name=_('location')
    )
    
    # Treatment plan (for phased treatments)
    parent_treatment = models.ForeignKey(
        'self', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='follow_up_treatments',
        verbose_name=_('parent treatment')
    )
    phase_number = models.PositiveSmallIntegerField(_('phase number'), default=1)
    
    # Metadata
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.PROTECT,
        related_name='created_treatments',
        verbose_name=_('created by')
    )
    
    def __str__(self):
        return f"{self.catalog_item} for {self.patient} on {self.scheduled_date.date()}"
    
    def complete(self):
        """Mark the treatment as completed"""
        self.status = 'COMPLETED'
        self.completed_date = timezone.now()
        self.save()
    
    def cancel(self):
        """Mark the treatment as canceled"""
        self.status = 'CANCELED'
        self.save()
    
    class Meta:
        verbose_name = _('treatment')
        verbose_name_plural = _('treatments')
        ordering = ['-scheduled_date']

class TreatmentNote(models.Model):
    """
    Additional notes or observations made during treatment
    Multiple notes can be added per treatment
    """
    NOTE_TYPE_CHOICES = [
        ('DOCTOR', _('Doctor Note')),
        ('BILLING', _('Billing Note')),
        ('RESCHEDULE', _('Reschedule Note')),
    ]
    
    treatment = models.ForeignKey(Treatment, on_delete=models.CASCADE, related_name='additional_notes', verbose_name=_('treatment'))
    date = models.DateTimeField(_('date'), default=timezone.now)
    note = models.TextField(_('note'))
    type = models.CharField(_('type'), max_length=20, choices=NOTE_TYPE_CHOICES, default='DOCTOR')  # Move type field up
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, verbose_name=_('created by'))

    def __str__(self):
        return f"{self.get_type_display()} for {self.treatment} on {self.date}"  # Better __str__ to show type
    
    class Meta:
        verbose_name = _('treatment note')
        verbose_name_plural = _('treatment notes')
        ordering = ['-date']

class TreatmentScheduleHistory(models.Model):
    treatment = models.ForeignKey(Treatment, on_delete=models.CASCADE, related_name='schedule_history', verbose_name=_('treatment'))
    scheduled_date = models.DateTimeField(_('scheduled date'))
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    
    def __str__(self):
        return f"{self.treatment} scheduled for {self.scheduled_date}"
    
    class Meta:
        verbose_name = _('schedule history')
        verbose_name_plural = _('schedule histories')
        ordering = ['-created_at']
        
class TreatmentDetail(models.Model):
    """
    Flexible model to store specialty-specific treatment details
    using a key-value approach
    """
    
    treatment = models.ForeignKey(
        Treatment, 
        on_delete=models.CASCADE, 
        related_name='details',
        verbose_name=_('treatment')
    )
    field_name = models.CharField(_('field name'), max_length=100)
    field_value = models.TextField(_('field value'), blank=True)
    
    def __str__(self):
        return f"{self.field_name}: {self.field_value}"
    
    class Meta:
        verbose_name = _('treatment detail')
        verbose_name_plural = _('treatment details')
        unique_together = ['treatment', 'field_name']  # Each field can appear only once per treatment