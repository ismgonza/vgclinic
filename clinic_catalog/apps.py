# clinic_catalog/apps.py
from django.apps import AppConfig

class ClinicCatalogConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'clinic_catalog'
    
    def ready(self):
        import clinic_catalog.signals  # Import signals