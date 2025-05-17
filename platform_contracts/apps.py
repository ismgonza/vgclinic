# platform_contracts/apps.py
from django.apps import AppConfig

class PlatformContractsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'platform_contracts'
    
    def ready(self):
        import platform_contracts.signals  # Import signals