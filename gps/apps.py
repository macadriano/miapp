from django.apps import AppConfig


class GpsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'gps'
    
    def ready(self):
        # Importar señales cuando la aplicación esté lista
        import gps.signals