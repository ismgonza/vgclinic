from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.translation import gettext_lazy as _
from django.core.validators import RegexValidator

class UserManager(BaseUserManager):
    """Custom user manager to use email as the username field."""
    def create_user(self, email, id_number, id_type, password=None, **extra_fields):
        """Create and save a regular user with the given email and password."""
        if not email:
            raise ValueError(_('The Email field must be set'))
        if not id_number:
            raise ValueError(_('The ID Number field must be set'))
        
        email = self.normalize_email(email)
        user = self.model(email=email, id_number=id_number, id_type=id_type, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, id_number, id_type, password=None, **extra_fields):
        """Create and save a SuperUser with the given email and password."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))
        
        return self.create_user(email, id_number, id_type, password, **extra_fields)

class User(AbstractUser):
    """Custom user model that uses email as username and ID number as primary key."""
    ID_TYPE_CHOICES = [
        ('cedula', _('Cédula')),
        ('dimex', _('DIMEX')),
    ]
    
    username = None  # Remove username field
    id = models.BigAutoField(primary_key=True)  # Use standard auto ID instead of custom primary key
    
    id_type = models.CharField(
        _('ID Type'),
        max_length=6,
        choices=ID_TYPE_CHOICES,
        default='cedula'
    )
    
    # Validators to ensure correct format
    cedula_validator = RegexValidator(
        regex=r'^\d{9}$',
        message=_('Cédula must be exactly 9 digits')
    )
    dimex_validator = RegexValidator(
        regex=r'^\d{11,12}$',
        message=_('DIMEX must be 11 or 12 digits')
    )
    
    id_number = models.CharField(
        _('ID Number'),
        max_length=12,
        unique=True,
        help_text=_('Cédula (9 digits) or DIMEX (11-12 digits)')
    )
    
    email = models.EmailField(_('Email Address'), unique=True)
    
    # Set email as the USERNAME_FIELD (used for login)
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['id_number', 'id_type', 'first_name', 'last_name']
    
    objects = UserManager()
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email})"
    
    def clean(self):
        """Validate the ID number based on the ID type."""
        from django.core.exceptions import ValidationError
        
        if self.id_type == 'cedula':
            try:
                self.cedula_validator(self.id_number)
                # Pad with zeros to get 12 digits for internal storage
                self.id_number = self.id_number.zfill(12)
            except ValidationError:
                raise ValidationError(_('Cédula must be exactly 9 digits'))
        elif self.id_type == 'dimex':
            try:
                self.dimex_validator(self.id_number)
                # Ensure it's 12 digits by padding if needed
                self.id_number = self.id_number.zfill(12)
            except ValidationError:
                raise ValidationError(_('DIMEX must be 11 or 12 digits'))
    
    def save(self, *args, **kwargs):
        # Normalize the ID number before saving (pad with zeros)
        self.id_number = self.id_number.zfill(12)
        super().save(*args, **kwargs)
    
    def get_display_id(self):
        """Return the ID in the format appropriate for display."""
        if self.id_type == 'cedula':
            # Remove leading zeros for display
            return self.id_number.lstrip('0')
        else:
            # For DIMEX, keep as is
            return self.id_number.lstrip('0')
    
    class Meta:
        verbose_name = _('User')
        verbose_name_plural = _('Users')