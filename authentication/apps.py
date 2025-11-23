from django.apps import AppConfig


class AuthenticationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'authentication'
    verbose_name = 'Autenticación y Usuarios'
    
    def ready(self):
        # Importar signals cuando la app esté lista
        import authentication.models  # noqa
