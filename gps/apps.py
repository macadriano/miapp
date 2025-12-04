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
            import logging
            logger = logging.getLogger(__name__)
            
            logger.info(f"🔵 [APPS] GpsConfig.ready() ejecutado. sys.argv: {sys.argv}")
            
            # Evitar ejecutar en comandos de gestión que no sean runserver
            # También evitar en producción con Gunicorn para evitar loops de reinicio
            if 'runserver' in sys.argv:
                logger.info("🔵 [APPS] Modo runserver detectado, iniciando receptores activos...")
                from gps.receiver_manager import start_active_receivers
                import threading
                
                # Iniciar en un hilo separado para no bloquear el inicio de Django
                # Solo una vez, no periódicamente
                thread = threading.Thread(target=start_active_receivers, daemon=True, name="AutoStartReceivers")
                thread.start()
                logger.info(f"✅ [APPS] Hilo de auto-inicio de receptores iniciado. Thread ID: {thread.ident}")
            else:
                logger.info(f"ℹ️ [APPS] No es modo runserver, omitiendo auto-inicio de receptores")
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"❌ [APPS] No se pudieron iniciar los receptores automáticos: {e}")
            import traceback
            logger.error(traceback.format_exc())
            print(f"⚠️ No se pudieron iniciar los receptores automáticos: {e}")