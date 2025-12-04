"""
Módulo para gestionar múltiples receptores GPS (TCP, UDP, HTTP)
"""

import threading
from typing import Optional, Dict
from gps.receivers.tcp_receiver import TCPReceiver

# Diccionario de receptores activos: {puerto: {receiver, thread}}
_active_receivers: Dict[int, dict] = {}


def get_receiver(port: int) -> Optional[TCPReceiver]:
    """Obtener la instancia del receptor para un puerto específico"""
    if port in _active_receivers:
        return _active_receivers[port]['receiver']
    return None


def is_receiver_running(port: int) -> bool:
    """Verificar si un receptor está corriendo en un puerto específico"""
    if port in _active_receivers:
        receiver = _active_receivers[port]['receiver']
        return receiver is not None and receiver.running
    return False


def get_all_running_receivers() -> dict:
    """Obtener todos los receptores activos"""
    result = {}
    for port, data in _active_receivers.items():
        if data['receiver'].running:
            result[port] = {
                'port': port,
                'stats': data['receiver'].get_stats()
            }
    return result



def start_active_receivers():
    """
    Iniciar todos los receptores que estén marcados como activos en la base de datos.
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("🔄 [AUTO-START] start_active_receivers() llamado")
        print("🔄 [AUTO-START] Iniciando receptores activos...")
        
        from gps.models import ConfiguracionReceptor
        
        # Obtener todos los receptores activos
        receptores = ConfiguracionReceptor.objects.filter(activo=True)
        count = receptores.count()
        
        logger.info(f"🔄 [AUTO-START] Encontrados {count} receptores activos en BD")
        print(f"🔄 Iniciando {count} receptores activos...")
        
        for receptor in receptores:
            logger.info(f"🔄 [AUTO-START] Procesando receptor: {receptor.nombre} (puerto {receptor.puerto})")
            # Verificar si ya está corriendo para no duplicar
            if is_receiver_running(receptor.puerto):
                logger.info(f"ℹ️ [AUTO-START] Receptor en puerto {receptor.puerto} ya está corriendo, omitiendo")
                print(f"   ℹ️ Receptor en puerto {receptor.puerto} ya está corriendo")
                continue
                
            logger.info(f"➡️ [AUTO-START] Iniciando receptor {receptor.nombre} en puerto {receptor.puerto}...")
            print(f"   ➡️ Iniciando receptor {receptor.nombre} en puerto {receptor.puerto}...")
            # Usar start_receiver pero evitar recursión infinita de actualizaciones de DB si fuera necesario
            # En este caso start_receiver es seguro
            result = start_receiver(port=receptor.puerto)
            logger.info(f"📊 [AUTO-START] Resultado de start_receiver: {result}")
            
        logger.info(f"✅ [AUTO-START] start_active_receivers() completado")
            
    except Exception as e:
        logger.error(f"❌ [AUTO-START] Error iniciando receptores activos: {e}")
        import traceback
        logger.error(traceback.format_exc())
        print(f"❌ Error iniciando receptores activos: {e}")


def start_receiver(host: str = '0.0.0.0', port: int = 5003) -> dict:
    """
    Iniciar un receptor en un puerto específico
    
    Args:
        host: Dirección IP donde escuchar
        port: Puerto donde escuchar
    
    Returns:
        Diccionario con el estado de la operación
    """
    import logging
    logger = logging.getLogger(__name__)
    
    global _active_receivers
    
    logger.info(f"🚀 [MANAGER] start_receiver() llamado para puerto {port}")
    print(f"🚀 [MANAGER] Iniciando receptor en puerto {port}")
    
    # Verificar si ya hay un receptor corriendo en este puerto
    if is_receiver_running(port):
        logger.warning(f"⚠️ [MANAGER] Ya existe un receptor activo en el puerto {port}")
        return {
            'success': False,
            'message': f'Ya existe un receptor activo en el puerto {port}',
            'stats': None
        }
    
    logger.info(f"🚀 [MANAGER] No hay receptor activo en puerto {port}, procediendo a iniciar...")
    
    try:
        logger.info(f"🚀 [MANAGER] Verificando configuración del receptor en puerto {port}...")
        # Asegurar que existe la configuración del receptor
        from gps.models import ConfiguracionReceptor, TipoEquipoGPS
        
        # Verificar si existe la configuración
        try:
            config = ConfiguracionReceptor.objects.get(puerto=port)
            logger.info(f"🚀 [MANAGER] Config encontrada: {config.nombre}, activo={config.activo}")
            # Asegurar que esté marcado como activo
            if not config.activo:
                logger.info(f"🚀 [MANAGER] Marcando receptor como activo en BD...")
                config.activo = True
                config.save()
                logger.info(f"✅ [MANAGER] Receptor marcado como activo en BD")
            else:
                logger.info(f"ℹ️ [MANAGER] Receptor ya estaba marcado como activo en BD")
        except ConfiguracionReceptor.DoesNotExist:
            logger.info(f"🚀 [MANAGER] No existe configuración, creando una nueva...")
            # Crear configuración por defecto
            try:
                tipo_equipo = TipoEquipoGPS.objects.first()
                if not tipo_equipo:
                    tipo_equipo = TipoEquipoGPS.objects.create(
                        codigo='TQ',
                        nombre='Queclink TQ',
                        fabricante='Queclink',
                        protocolo='TCP',
                        puerto_default=5003,
                        formato_datos={'type': 'binary'},
                        activo=True
                    )
                
                ConfiguracionReceptor.objects.create(
                    nombre=f'Receptor Puerto {port}',
                    tipo_equipo=tipo_equipo,
                    puerto=port,
                    transporte='TCP',
                    protocolo='TQ',
                    activo=True,
                    max_conexiones=100,
                    max_equipos=1000,
                    timeout=30,
                    region='ARG',
                    prioridad=1
                )
            except Exception as e:
                pass
        
        logger.info(f"🚀 [MANAGER] Creando instancia de TCPReceiver para puerto {port}...")
        # Crear nueva instancia del receptor
        receiver = TCPReceiver(host=host, port=port)
        logger.info(f"✅ [MANAGER] Instancia de TCPReceiver creada. running={receiver.running}")
        
        # Iniciar en un hilo separado con manejo de errores mejorado
        def run_receiver():
            import logging
            thread_logger = logging.getLogger(__name__)
            thread_logger.info(f"🧵 [THREAD {port}] Hilo del receptor iniciado. Thread ID: {threading.current_thread().ident}")
            try:
                thread_logger.info(f"🧵 [THREAD {port}] Llamando a receiver.start()...")
                receiver.start()
                thread_logger.info(f"🧵 [THREAD {port}] receiver.start() finalizó normalmente")
            except Exception as e:
                thread_logger.error(f"❌ [THREAD {port}] Error crítico en receptor: {e}")
                import traceback
                thread_logger.error(traceback.format_exc())
                # Actualizar BD para evitar auto-reinicio
                try:
                    from gps.models import ConfiguracionReceptor
                    config = ConfiguracionReceptor.objects.get(puerto=port)
                    if config.activo:
                        config.activo = False
                        config.save()
                        thread_logger.info(f"✅ [THREAD {port}] Receptor marcado como inactivo debido a error crítico")
                except Exception as db_error:
                    thread_logger.warning(f"⚠️ [THREAD {port}] No se pudo actualizar BD: {db_error}")
            finally:
                thread_logger.info(f"🧵 [THREAD {port}] Hilo del receptor finalizado")
        
        logger.info(f"🚀 [MANAGER] Creando hilo para receptor en puerto {port}...")
        thread = threading.Thread(target=run_receiver, name=f"TCPReceiver-{port}")
        thread.daemon = False  # Cambiar a False para que el hilo no termine con el proceso principal
        thread.start()
        logger.info(f"✅ [MANAGER] Hilo iniciado. Thread ID: {thread.ident}, Name: {thread.name}, Daemon: {thread.daemon}")
        
        # Guardar en el diccionario de receptores activos
        _active_receivers[port] = {
            'receiver': receiver,
            'thread': thread,
            'host': host
        }
        logger.info(f"✅ [MANAGER] Receptor agregado a _active_receivers. Total activos: {len(_active_receivers)}")
        
        # Dar tiempo para que inicie y verificar que realmente está corriendo
        import time
        logger.info(f"🚀 [MANAGER] Esperando 1 segundo para que el receptor inicie...")
        time.sleep(1)
        
        # Verificar que el receptor realmente está corriendo
        logger.info(f"🚀 [MANAGER] Verificando estado del receptor. running={receiver.running}")
        if not receiver.running:
            logger.error(f"❌ [MANAGER] El receptor no está corriendo después de iniciar. running={receiver.running}")
            # Si no está corriendo, remover del diccionario y retornar error
            if port in _active_receivers:
                del _active_receivers[port]
                logger.info(f"🗑️ [MANAGER] Receptor removido de _active_receivers")
            return {
                'success': False,
                'message': f'El receptor no pudo iniciar correctamente en {host}:{port}',
                'stats': None
            }
        
        logger.info(f"✅ [MANAGER] Receptor iniciado correctamente. running={receiver.running}")
        stats = receiver.get_stats()
        logger.info(f"📊 [MANAGER] Estadísticas del receptor: {stats}")
        return {
            'success': True,
            'message': f'Receptor iniciado en {host}:{port}',
            'stats': stats
        }
        
    except Exception as e:
        return {
            'success': False,
            'message': f'Error iniciando receptor: {str(e)}',
            'stats': None
        }


def stop_receiver(port: int) -> dict:
    """
    Detener un receptor en un puerto específico
    
    Args:
        port: Puerto del receptor a detener
    
    Returns:
        Diccionario con el estado de la operación
    """
    import logging
    logger = logging.getLogger(__name__)
    
    global _active_receivers
    
    logger.info(f"🛑 [MANAGER] stop_receiver() llamado para puerto {port}")
    print(f"🛑 [MANAGER] Deteniendo receptor en puerto {port}")
    
    if port not in _active_receivers:
        logger.warning(f"⚠️ [MANAGER] No hay receptor activo en el puerto {port}. Receptores activos: {list(_active_receivers.keys())}")
        return {
            'success': False,
            'message': f'No hay receptor activo en el puerto {port}',
            'stats': None
        }
    
    try:
        logger.info(f"🛑 [MANAGER] Obteniendo datos del receptor en puerto {port}...")
        data = _active_receivers[port]
        receiver = data['receiver']
        thread = data['thread']
        
        logger.info(f"🛑 [MANAGER] Receptor encontrado. running={receiver.running if receiver else 'N/A'}, thread_alive={thread.is_alive() if thread else 'N/A'}")
        
        # Detener el receptor
        logger.info(f"🛑 [MANAGER] Llamando a receiver.stop()...")
        receiver.stop(update_db_on_error=False)  # No actualizar BD aquí, lo haremos manualmente
        logger.info(f"🛑 [MANAGER] receiver.stop() completado. running={receiver.running if receiver else 'N/A'}")
        
        # Esperar a que termine el hilo
        if thread:
            logger.info(f"🛑 [MANAGER] Esperando a que termine el hilo (timeout 2s)...")
            thread.join(timeout=2)
            logger.info(f"🛑 [MANAGER] Hilo finalizado. thread_alive={thread.is_alive()}")
            
        # Actualizar estado en base de datos
        logger.info(f"🛑 [MANAGER] Actualizando estado en BD...")
        try:
            from gps.models import ConfiguracionReceptor
            config = ConfiguracionReceptor.objects.get(puerto=port)
            logger.info(f"🛑 [MANAGER] Config encontrada. activo actual: {config.activo}")
            config.activo = False
            config.save()
            logger.info(f"✅ [MANAGER] Receptor marcado como inactivo en BD")
        except Exception as e:
            logger.warning(f"⚠️ [MANAGER] No se pudo actualizar estado en BD para puerto {port}: {e}")
            import traceback
            logger.warning(traceback.format_exc())

        
        stats = receiver.get_stats() if receiver else None
        logger.info(f"📊 [MANAGER] Estadísticas finales: {stats}")
        
        # Remover del diccionario
        logger.info(f"🗑️ [MANAGER] Removiendo receptor de _active_receivers...")
        del _active_receivers[port]
        logger.info(f"✅ [MANAGER] Receptor removido. Total activos: {len(_active_receivers)}")
        
        return {
            'success': True,
            'message': f'Receptor detenido en puerto {port}',
            'stats': stats
        }
        
    except Exception as e:
        logger.error(f"❌ [MANAGER] Error deteniendo receptor: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return {
            'success': False,
            'message': f'Error deteniendo receptor: {str(e)}',
            'stats': None
        }


def get_receiver_stats(port: Optional[int] = None) -> dict:
    """
    Obtener estadísticas de un receptor específico o de todos los activos
    
    Args:
        port: Puerto del receptor. Si es None, retorna stats de todos los receptores activos
    
    Returns:
        Diccionario con las estadísticas
    """
    if port is not None:
        # Stats de un puerto específico
        if port in _active_receivers and _active_receivers[port]['receiver'].running:
            receiver = _active_receivers[port]['receiver']
            stats = receiver.get_stats()
            if stats:
                stats['port'] = port
            return stats
        return None
    else:
        # Stats de todos los receptores activos
        result = {
            'running': len([r for r in _active_receivers.values() if r['receiver'].running]) > 0,
            'ports': list(_active_receivers.keys()),
            'receivers': {}
        }
        
        for port, data in _active_receivers.items():
            if data['receiver'].running:
                stats = data['receiver'].get_stats()
                if stats:
                    stats['port'] = port
                    result['receivers'][port] = stats
        
        # Si solo hay un receptor, agregar stats individuales para compatibilidad
        if len(result['receivers']) == 1:
            port = list(result['receivers'].keys())[0]
            stats = result['receivers'][port]
            result.update(stats)
        
        return result
