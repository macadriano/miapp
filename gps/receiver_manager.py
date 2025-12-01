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
    try:
        from gps.models import ConfiguracionReceptor
        
        # Obtener todos los receptores activos
        receptores = ConfiguracionReceptor.objects.filter(activo=True)
        
        print(f"🔄 Iniciando {receptores.count()} receptores activos...")
        
        for receptor in receptores:
            # Verificar si ya está corriendo para no duplicar
            if is_receiver_running(receptor.puerto):
                print(f"   ℹ️ Receptor en puerto {receptor.puerto} ya está corriendo")
                continue
                
            print(f"   ➡️ Iniciando receptor {receptor.nombre} en puerto {receptor.puerto}...")
            # Usar start_receiver pero evitar recursión infinita de actualizaciones de DB si fuera necesario
            # En este caso start_receiver es seguro
            start_receiver(port=receptor.puerto)
            
    except Exception as e:
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
    global _active_receivers
    
    # Verificar si ya hay un receptor corriendo en este puerto
    if is_receiver_running(port):
        return {
            'success': False,
            'message': f'Ya existe un receptor activo en el puerto {port}',
            'stats': None
        }
    
    try:
        # Asegurar que existe la configuración del receptor
        from gps.models import ConfiguracionReceptor, TipoEquipoGPS
        
        # Verificar si existe la configuración
        try:
            config = ConfiguracionReceptor.objects.get(puerto=port)
            # Asegurar que esté marcado como activo
            if not config.activo:
                config.activo = True
                config.save()
        except ConfiguracionReceptor.DoesNotExist:
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
        
        # Crear nueva instancia del receptor
        receiver = TCPReceiver(host=host, port=port)
        
        # Iniciar en un hilo separado con manejo de errores mejorado
        def run_receiver():
            try:
                receiver.start()
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error crítico en receptor {port}: {e}")
                import traceback
                logger.error(traceback.format_exc())
                # Actualizar BD para evitar auto-reinicio
                try:
                    from gps.models import ConfiguracionReceptor
                    config = ConfiguracionReceptor.objects.get(puerto=port)
                    if config.activo:
                        config.activo = False
                        config.save()
                        logger.info(f"Receptor en puerto {port} marcado como inactivo debido a error crítico")
                except Exception as db_error:
                    logger.warning(f"No se pudo actualizar BD: {db_error}")
        
        thread = threading.Thread(target=run_receiver)
        thread.daemon = False  # Cambiar a False para que el hilo no termine con el proceso principal
        thread.start()
        
        # Guardar en el diccionario de receptores activos
        _active_receivers[port] = {
            'receiver': receiver,
            'thread': thread,
            'host': host
        }
        
        # Dar tiempo para que inicie y verificar que realmente está corriendo
        import time
        time.sleep(1)
        
        # Verificar que el receptor realmente está corriendo
        if not receiver.running:
            # Si no está corriendo, remover del diccionario y retornar error
            if port in _active_receivers:
                del _active_receivers[port]
            return {
                'success': False,
                'message': f'El receptor no pudo iniciar correctamente en {host}:{port}',
                'stats': None
            }
        
        return {
            'success': True,
            'message': f'Receptor iniciado en {host}:{port}',
            'stats': receiver.get_stats()
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
    global _active_receivers
    
    if port not in _active_receivers:
        return {
            'success': False,
            'message': f'No hay receptor activo en el puerto {port}',
            'stats': None
        }
    
    try:
        data = _active_receivers[port]
        receiver = data['receiver']
        thread = data['thread']
        
        # Detener el receptor
        receiver.stop()
        
        # Esperar a que termine el hilo
        if thread:
            thread.join(timeout=2)
            
        # Actualizar estado en base de datos
        try:
            from gps.models import ConfiguracionReceptor
            config = ConfiguracionReceptor.objects.get(puerto=port)
            config.activo = False
            config.save()
        except Exception as e:
            print(f"⚠️ No se pudo actualizar estado en BD para puerto {port}: {e}")

        
        stats = receiver.get_stats() if receiver else None
        
        # Remover del diccionario
        del _active_receivers[port]
        
        return {
            'success': True,
            'message': f'Receptor detenido en puerto {port}',
            'stats': stats
        }
        
    except Exception as e:
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
