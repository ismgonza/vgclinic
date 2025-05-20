# clinic_patients/models.py
from django.db import models
from django.utils import timezone
from platform_accounts.models import Account  # Assuming this is your clinic/account model

class Patient(models.Model):
    """
    Core patient model with personal information that can be shared across clinics
    """
    GENDER_CHOICES = [
        ('M', 'Masculine'),
        ('F', 'Feminine'),
        ('O', 'Other'),
    ]
    
    MARITAL_STATUS_CHOICES = [
        ('S', 'Single'),
        ('M', 'Married'),
        ('D', 'Divorced'),
        ('W', 'Widow'),
    ]
    
    # Personal identification
    id_number = models.CharField(max_length=30, unique=True)
    is_foreign = models.BooleanField(default=False)
    
    # Personal details
    first_name = models.CharField(max_length=100)
    last_name1 = models.CharField(max_length=100)
    last_name2 = models.CharField(max_length=100, blank=True)
    
    birth_date = models.DateField()
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    marital_status = models.CharField(max_length=1, choices=MARITAL_STATUS_CHOICES)
    
    email = models.EmailField(blank=True)
    
    # Address information
    province = models.CharField(max_length=100)
    canton = models.CharField(max_length=100)
    district = models.CharField(max_length=100)
    address = models.TextField()
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.first_name} {self.last_name1} {self.last_name2}".strip()


class PatientPhone(models.Model):
    """Patient phone numbers - shared across clinics"""
    PHONE_TYPE_CHOICES = [
        ('P', 'Personal'),
        ('H', 'Home'),
        ('W', 'Work'),
        ('O', 'Other'),
    ]
    
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='phones')
    phone_number = models.CharField(max_length=20)
    phone_type = models.CharField(max_length=1, choices=PHONE_TYPE_CHOICES, default='P')
    
    def __str__(self):
        return f"{self.get_phone_type_display()}: {self.phone_number}"


class EmergencyContact(models.Model):
    """Emergency contacts - shared across clinics"""
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='emergency_contacts')
    first_name = models.CharField(max_length=100)
    last_name1 = models.CharField(max_length=100)
    last_name2 = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=20)
    relationship = models.CharField(max_length=50, blank=True)
    
    def __str__(self):
        return f"{self.first_name} {self.last_name1}"


class PatientAccount(models.Model):
    """
    Links patients to specific accounts (clinics) and stores clinic-specific information
    """
    REFERRAL_SOURCE_CHOICES = [
        ('INT', 'Internet Search'),
        ('SOC', 'Social Media'),
        ('REC', 'Recommendation'),
        ('OAD', 'Online Advertisement'),
        ('OUT', 'Outdoor Advertisement'),
        ('OTH', 'Other'),
    ]
    
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='clinic_memberships')
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='patients')
    
    # Clinic-specific patient information
    admission_date = models.DateTimeField(default=timezone.now)
    referral_source = models.CharField(max_length=3, choices=REFERRAL_SOURCE_CHOICES, blank=True)
    consultation_reason = models.TextField(blank=True)
    receive_notifications = models.BooleanField(default=False)
    
    # Additional metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['patient', 'account']  # A patient can only be linked once to each account
    
    def __str__(self):
        return f"{self.patient} at {self.account}"


class MedicalHistory(models.Model):
    """
    Medical history is specific to a patient-account relationship
    """
    patient_account = models.ForeignKey(PatientAccount, on_delete=models.CASCADE, related_name='medical_histories')
    created_at = models.DateTimeField(default=timezone.now)
    
    # Medical History
    under_treatment = models.BooleanField(default=False)
    under_treatment_text = models.TextField(blank=True)
    current_medication = models.BooleanField(default=False)
    current_medication_text = models.TextField(blank=True)
    serious_illnesses = models.BooleanField(default=False)
    serious_illnesses_text = models.TextField(blank=True)
    surgeries = models.BooleanField(default=False)
    surgeries_text = models.TextField(blank=True)
    allergies = models.BooleanField(default=False)
    allergies_text = models.TextField(blank=True)
    anesthesia_issues = models.BooleanField(default=False)
    bleeding_issues = models.BooleanField(default=False)
    pregnant_or_lactating = models.BooleanField(default=False)
    contraceptives = models.BooleanField(default=False)
    
    # Medical Conditions
    high_blood_pressure = models.BooleanField(default=False)
    rheumatic_fever = models.BooleanField(default=False)
    drug_addiction = models.BooleanField(default=False)
    diabetes = models.BooleanField(default=False)
    anemia = models.BooleanField(default=False)
    thyroid = models.BooleanField(default=False)
    asthma = models.BooleanField(default=False)
    arthritis = models.BooleanField(default=False)
    cancer = models.BooleanField(default=False)
    heart_problems = models.BooleanField(default=False)
    smoker = models.BooleanField(default=False)
    ulcers = models.BooleanField(default=False)
    gastritis = models.BooleanField(default=False)
    hepatitis = models.BooleanField(default=False)
    kidney_diseases = models.BooleanField(default=False)
    hormonal_problems = models.BooleanField(default=False)
    epilepsy = models.BooleanField(default=False)
    aids = models.BooleanField(default=False)
    psychiatric_treatment = models.BooleanField(default=False)
    
    # Confirmation
    information_confirmed = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-created_at']
        # This ensures we can have multiple medical histories per patient-account, but only one per date
        unique_together = ['patient_account', 'created_at']
    
    def __str__(self):
        return f"Medical history for {self.patient_account.patient} at {self.patient_account.account} - {self.created_at.date()}"