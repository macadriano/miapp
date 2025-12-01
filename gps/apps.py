from django.apps import AppConfig

class GpsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'gps'

    def ready(self):
        # Importar señales cuando la aplicación esté lista
        import gps.signals
        
        # Iniciar receptores activos
        # Usamos un try/except para evitar problemas durante migraciones o comandos de gestión
        try:
            import sys
            # Evitar ejecutar en comandos de gestión que no sean runserver
            # También evitar en producción con Gunicorn para evitar loops de reinicio
            if 'runserver' in sys.argv:
                from gps.receiver_manager import start_active_receivers
                import threading
                
                # Iniciar en un hilo separado para no bloquear el inicio de Django
                # Solo una vez, no periódicamente
                threading.Thread(target=start_active_receivers, daemon=True).start()
        except Exception as e:
            print(f"⚠️ No se pudieron iniciar los receptores automáticos: {e}")