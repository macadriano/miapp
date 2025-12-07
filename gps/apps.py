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
            
            # Comandos de gestión que NO deben iniciar receptores
            comandos_gestion = ['migrate', 'makemigrations', 'collectstatic', 'createsuperuser', 
                              'shell', 'test', 'flush', 'dumpdata', 'loaddata', 'check']
            
            # Verificar si estamos en un comando de gestión
            es_comando_gestion = any(cmd in sys.argv for cmd in comandos_gestion)
            
            # Iniciar receptores si:
            # 1. Es runserver (desarrollo)
            # 2. Es gunicorn/uwsgi (producción) - detectado por presencia de 'gunicorn' o 'uwsgi' en sys.argv
            # 3. NO es un comando de gestión
            es_servidor_wsgi = 'gunicorn' in ' '.join(sys.argv) or 'uwsgi' in ' '.join(sys.argv)
            es_runserver = 'runserver' in sys.argv
            
            if (es_runserver or es_servidor_wsgi) and not es_comando_gestion:
                modo = "runserver" if es_runserver else "gunicorn/uwsgi"
                logger.info(f"🔵 [APPS] Modo {modo} detectado, iniciando receptores activos desde BD...")
                from gps.receiver_manager import start_active_receivers
                import threading
                
                # Iniciar en un hilo separado para no bloquear el inicio de Django
                # Solo una vez, no periódicamente
                thread = threading.Thread(target=start_active_receivers, daemon=True, name="AutoStartReceivers")
                thread.start()
                logger.info(f"✅ [APPS] Hilo de auto-inicio de receptores iniciado. Thread ID: {thread.ident}")
            else:
                if es_comando_gestion:
                    logger.info(f"ℹ️ [APPS] Comando de gestión detectado, omitiendo auto-inicio de receptores")
                else:
                    logger.info(f"ℹ️ [APPS] Modo desconocido, omitiendo auto-inicio de receptores")
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"❌ [APPS] No se pudieron iniciar los receptores automáticos: {e}")
            import traceback
            logger.error(traceback.format_exc())
            print(f"⚠️ No se pudieron iniciar los receptores automáticos: {e}")