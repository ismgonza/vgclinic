# clinic_staff/models.py
from django.db import models
from django.utils.translation import gettext_lazy as _
from platform_accounts.models import Account, AccountUser
from clinic_locations.models import Location

class StaffSpecialty(models.Model):
    """
    Represents specialties or qualifications for staff members.
    """
    account = models.ForeignKey(
        Account, 
        on_delete=models.CASCADE, 
        related_name='specialties',
        verbose_name=_('account')
    )
    name = models.CharField(_('name'), max_length=100)
    description = models.TextField(_('description'), blank=True)
    is_active = models.BooleanField(_('active'), default=True)
    
    # Metadata
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    class Meta:
        verbose_name = _('specialty')
        verbose_name_plural = _('specialties')
        ordering = ['name']
        unique_together = [['account', 'name']]
    
    def __str__(self):
        return f"{self.name} ({self.account.name})"

class StaffMember(models.Model):
    """
    Represents a staff member in a clinic with their role and details.
    """
    # Role codes for internationalization
    ROLE_DOCTOR = 'doc'
    ROLE_ASSISTANT = 'asst'
    ROLE_RECEPTIONIST = 'recp'
    ROLE_ADMINISTRATOR = 'admn'
    ROLE_OTHER = 'othr'
    
    ROLE_CHOICES = (
        (ROLE_DOCTOR, _('Doctor')),
        (ROLE_ASSISTANT, _('Assistant')),
        (ROLE_RECEPTIONIST, _('Receptionist')),
        (ROLE_ADMINISTRATOR, _('Administrator')),
        (ROLE_OTHER, _('Other')),
    )
    
    account_user = models.OneToOneField(
        AccountUser,
        on_delete=models.CASCADE,
        related_name='staff_profile',
        verbose_name=_('account user')
    )
    job_title = models.CharField(_('job title'), max_length=100)
    staff_role = models.CharField(_('role'), max_length=20, choices=ROLE_CHOICES)
    specialties = models.ManyToManyField(
        StaffSpecialty,
        related_name='staff_members',
        blank=True,
        verbose_name=_('specialties')
    )
    license_number = models.CharField(_('license number'), max_length=50, blank=True)
    assigned_locations = models.ManyToManyField(
        Location,
        through='StaffLocation',
        related_name='assigned_staff',
        verbose_name=_('assigned locations')
    )
    
    # Contact information
    phone = models.CharField(_('phone'), max_length=20, blank=True)
    
    # Status
    is_active = models.BooleanField(_('active'), default=True)
    can_book_appointments = models.BooleanField(_('can book appointments'), default=True)
    
    # Appearance
    appointment_color = models.CharField(_('appointment color'), max_length=20, blank=True, 
                                      help_text=_('Color code for calendar display'))
    
    # Metadata
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    class Meta:
        verbose_name = _('staff member')
        verbose_name_plural = _('staff members')
        ordering = ['account_user__user__first_name', 'account_user__user__last_name']
    
    def __str__(self):
        user = self.account_user.user
        return f"{user.first_name} {user.last_name} - {self.get_staff_role_display()} ({self.account_user.account.name})"
    
    @property
    def full_name(self):
        user = self.account_user.user
        return f"{user.first_name} {user.last_name}"
    
    @property
    def email(self):
        return self.account_user.user.email

class StaffInvitation(models.Model):
    """
    Invitations for staff members to join a clinic.
    """
    # Status codes for internationalization
    STATUS_PENDING = 'pend'
    STATUS_ACCEPTED = 'acpt'
    STATUS_DECLINED = 'decl'
    STATUS_EXPIRED = 'expd'
    
    STATUS_CHOICES = (
        (STATUS_PENDING, _('Pending')),
        (STATUS_ACCEPTED, _('Accepted')),
        (STATUS_DECLINED, _('Declined')),
        (STATUS_EXPIRED, _('Expired')),
    )
    
    account = models.ForeignKey(
        'platform_accounts.Account',
        on_delete=models.CASCADE,
        related_name='staff_invitations',
        verbose_name=_('account')
    )
    email = models.EmailField(_('email'))
    role = models.CharField(_('role'), max_length=20, choices=StaffMember.ROLE_CHOICES)
    token = models.CharField(_('token'), max_length=64, unique=True)
    status = models.CharField(
        _('status'), 
        max_length=4, 
        choices=STATUS_CHOICES, 
        default=STATUS_PENDING
    )
    invited_by = models.ForeignKey(
        'platform_users.User',
        on_delete=models.SET_NULL,
        related_name='sent_staff_invitations',
        null=True,
        verbose_name=_('invited by')
    )
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    expires_at = models.DateTimeField(_('expires at'))
    
    # For existing users who are invited
    existing_user = models.BooleanField(_('existing user'), default=False)
    
    class Meta:
        verbose_name = _('staff invitation')
        verbose_name_plural = _('staff invitations')
        unique_together = (('email', 'account'),)

class StaffLocation(models.Model):
    """
    Links staff members to locations they work at with specific details.
    """
    staff = models.ForeignKey(
        StaffMember,
        on_delete=models.CASCADE,
        related_name='location_assignments',
        verbose_name=_('staff member')
    )
    location = models.ForeignKey(
        Location,
        on_delete=models.CASCADE,
        related_name='staff_assignments',
        verbose_name=_('location')
    )
    is_primary = models.BooleanField(_('primary location'), default=False)
    
    # Metadata
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('staff location')
        verbose_name_plural = _('staff locations')
        unique_together = [['staff', 'location']]
        ordering = ['-is_primary', 'location__name']
    
    def __str__(self):
        return f"{self.staff.full_name} @ {self.location.name}"
    
    def save(self, *args, **kwargs):
        """
        Ensure only one primary location per staff member.
        """
        if self.is_primary:
            # Set all other locations for this staff to non-primary
            StaffLocation.objects.filter(
                staff=self.staff, 
                is_primary=True
            ).exclude(pk=self.pk).update(is_primary=False)
        super().save(*args, **kwargs)


class AvailabilitySchedule(models.Model):
    """
    Defines the regular work schedule for a staff member.
    """
    DAYS_OF_WEEK = (
        (0, _('Monday')),
        (1, _('Tuesday')),
        (2, _('Wednesday')),
        (3, _('Thursday')),
        (4, _('Friday')),
        (5, _('Saturday')),
        (6, _('Sunday')),
    )
    
    staff = models.ForeignKey(
        StaffMember,
        on_delete=models.CASCADE,
        related_name='availability_schedules',
        verbose_name=_('staff member')
    )
    location = models.ForeignKey(
        Location,
        on_delete=models.CASCADE,
        related_name='staff_schedules',
        verbose_name=_('location')
    )
    day_of_week = models.PositiveSmallIntegerField(_('day of week'), choices=DAYS_OF_WEEK)
    start_time = models.TimeField(_('start time'))
    end_time = models.TimeField(_('end time'))
    is_available = models.BooleanField(_('available'), default=True)
    
    class Meta:
        verbose_name = _('availability schedule')
        verbose_name_plural = _('availability schedules')
        ordering = ['staff', 'location', 'day_of_week', 'start_time']
        unique_together = [['staff', 'location', 'day_of_week', 'start_time', 'end_time']]
    
    def __str__(self):
        return f"{self.staff.full_name} @ {self.location.name}: {self.get_day_of_week_display()} {self.start_time}-{self.end_time}"