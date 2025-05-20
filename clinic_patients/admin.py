# clinic_patients/admin.py
from django.contrib import admin
from .models import Patient, PatientPhone, EmergencyContact, MedicalHistory

class PatientPhoneInline(admin.TabularInline):
    model = PatientPhone
    extra = 1

class EmergencyContactInline(admin.TabularInline):
    model = EmergencyContact
    extra = 1

class MedicalHistoryInline(admin.StackedInline):
    model = MedicalHistory
    extra = 0
    max_num = 1
    fieldsets = (
        ('Medical History', {
            'fields': (
                ('under_treatment', 'under_treatment_text'),
                ('current_medication', 'current_medication_text'),
                ('serious_illnesses', 'serious_illnesses_text'),
                ('surgeries', 'surgeries_text'),
                ('allergies', 'allergies_text'),
            )
        }),
        ('Medical Status', {
            'fields': (
                ('anesthesia_issues', 'bleeding_issues'),
                ('pregnant_or_lactating', 'contraceptives'),
            )
        }),
        ('Medical Conditions', {
            'fields': (
                ('high_blood_pressure', 'rheumatic_fever', 'drug_addiction'),
                ('diabetes', 'anemia', 'thyroid'),
                ('asthma', 'arthritis', 'cancer'),
                ('heart_problems', 'smoker', 'ulcers'),
                ('gastritis', 'hepatitis', 'kidney_diseases'),
                ('hormonal_problems', 'epilepsy', 'aids'),
                ('psychiatric_treatment',),
            )
        }),
        ('Confirmation', {
            'fields': ('information_confirmed',)
        }),
    )

@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ('id', 'get_full_name', 'id_number', 'gender', 'birth_date', 'email', 'admission_date')
    list_filter = ('gender', 'marital_status', 'is_foreign', 'referral_source', 'province')
    search_fields = ('first_name', 'last_name1', 'last_name2', 'id_number', 'email')
    date_hierarchy = 'admission_date'
    
    fieldsets = (
        ('Personal Information', {
            'fields': (
                ('first_name', 'last_name1', 'last_name2'),
                ('id_number', 'is_foreign'),
                ('birth_date', 'gender', 'marital_status'),
                'email',
            )
        }),
        ('Address', {
            'fields': (
                ('province', 'canton', 'district'),
                'address',
            )
        }),
        ('Admission Details', {
            'fields': (
                'admission_date',
                'referral_source',
                'consultation_reason',
                'receive_notifications',
            )
        }),
    )
    
    inlines = [PatientPhoneInline, EmergencyContactInline, MedicalHistoryInline]
    
    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name1} {obj.last_name2}".strip()
    get_full_name.short_description = 'Full Name'

@admin.register(MedicalHistory)
class MedicalHistoryAdmin(admin.ModelAdmin):
    list_display = ('patient', 'created_at', 'information_confirmed')
    list_filter = ('created_at', 'information_confirmed')
    search_fields = ('patient__first_name', 'patient__last_name1', 'patient__id_number')
    date_hierarchy = 'created_at'
    
    # Similar fieldsets as the inline
    fieldsets = (
        ('Patient', {
            'fields': ('patient',)
        }),
        ('Medical History', {
            'fields': (
                ('under_treatment', 'under_treatment_text'),
                ('current_medication', 'current_medication_text'),
                ('serious_illnesses', 'serious_illnesses_text'),
                ('surgeries', 'surgeries_text'),
                ('allergies', 'allergies_text'),
            )
        }),
        ('Medical Status', {
            'fields': (
                ('anesthesia_issues', 'bleeding_issues'),
                ('pregnant_or_lactating', 'contraceptives'),
            )
        }),
        ('Medical Conditions', {
            'fields': (
                ('high_blood_pressure', 'rheumatic_fever', 'drug_addiction'),
                ('diabetes', 'anemia', 'thyroid'),
                ('asthma', 'arthritis', 'cancer'),
                ('heart_problems', 'smoker', 'ulcers'),
                ('gastritis', 'hepatitis', 'kidney_diseases'),
                ('hormonal_problems', 'epilepsy', 'aids'),
                ('psychiatric_treatment',),
            )
        }),
        ('Confirmation', {
            'fields': ('information_confirmed', 'created_at')
        }),
    )
    readonly_fields = ('created_at',)