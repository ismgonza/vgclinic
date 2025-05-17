from django.apps import AppConfig

class PlatformServicesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'platform_services'
    
    def ready(self):
        import platform_services.signals  # Import signals