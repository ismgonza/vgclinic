# clinic_staff/apps.py
from django.apps import AppConfig

class ClinicStaffConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'clinic_staff'
    
    def ready(self):
        import clinic_staff.signals  # Import signals