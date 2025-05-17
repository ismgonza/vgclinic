# clinic_locations/apps.py
from django.apps import AppConfig

class ClinicLocationsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'clinic_locations'
    
    def ready(self):
        import clinic_locations.signals  # Import signals