"""
Receptor TCP para equipos GPS con protocolo TQ
===============================================

Este módulo implementa un servidor TCP que recibe datos de equipos GPS
usando el protocolo TQ (Queclink) y los guarda en la base de datos.
"""

import os
import sys

# Configurar Django antes de importar módulos del proyecto
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wayproject.settings')

import django
django.setup()

import socket
import threading
import logging
from typing import Dict, Optional
from datetime import datetime

from django.utils import timezone

from gps.processors import ProcessorFactory
from gps.models import Posicion, Empresa, ConfiguracionReceptor, EstadisticasRecepcion
from moviles.models import Movil, MovilStatus, MovilGeocode
from gps.services import GeocodingService
from gps.logging_manager import logging_manager

logger = logging.getLogger(__name__)


class TCPReceiver:
    """
    Receptor TCP para equipos GPS con protocolo TQ.
    
    Escucha en un puerto TCP (por defecto 5003) y recibe datos de equipos GPS.
    Los datos se parsean usando el procesador apropiado y se guardan en la
    base de datos.
    """
    
    def __init__(self, host: str = '0.0.0.0', port: int = 5003, protocolo: str = 'TQ'):
        """
        Inicializar receptor TCP.
        
        Args:
            host: Dirección IP donde escuchar (0.0.0.0 = todas las interfaces)
            port: Puerto TCP donde escuchar (default: 5003)
            protocolo: Protocolo del receptor (default: TQ)
        """
        self.host = host
        self.port = port
        self.protocolo = protocolo
        self.server_socket = None
        self.running = False
        self.clients = {}
        self.processor = ProcessorFactory.get_processor('queclink')
        self.stats = {
            'total_connections': 0,
            'total_messages': 0,
            'successful_parses': 0,
            'failed_parses': 0,
            'database_errors': 0
        }
        
        # Configurar logger específico para este receptor
        self.receptor_logger = logging_manager.get_logger(port, 'TCP')
        
        # Registrar configuración del receptor
        self._register_configuration()
    
    def _register_configuration(self):
        """
        Registrar la configuración de este receptor en la base de datos.
        Se ejecuta al inicializar el receptor.
        """
        try:
            # Obtener o crear configuración de receptor
            receptor, created = ConfiguracionReceptor.objects.get_or_create(
                puerto=self.port,
                defaults={
                    'nombre': f'Receptor TCP Puerto {self.port}',
                    'protocolo': self.protocolo,
                    'activo': True,
                    'max_conexiones': 100,
                    'max_equipos': 1000,
                    'timeout': 30,
                    'tipo_equipo_id': 1,
                    'region': 'ARG'
                }
            )
            
            if created:
                logger.info(f"✅ Configuración de receptor creada: {receptor.nombre} en puerto {self.port}")
                print(f"✅ Configuración de receptor creada: {receptor.nombre} en puerto {self.port}")
            else:
                logger.info(f"📋 Usando configuración existente: {receptor.nombre} en puerto {self.port}")
                
        except Exception as e:
            logger.warning(f"No se pudo registrar configuración de receptor: {e}")
    
    def start(self):
        """
        Iniciar el servidor TCP.
        
        Este método bloquea hasta que el servidor sea detenido.
        """
        error_occurred = False
        try:
            # Crear socket TCP
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            
            self.running = True
            
            # Log de inicio
            self.receptor_logger.log_receptor_status(
                "INICIADO", 
                f"Escuchando en {self.host}:{self.port} - Protocolo: {self.protocolo}"
            )
            
            logger.info(f"✅ Receptor TCP iniciado en {self.host}:{self.port}")
            print(f"✅ Receptor TCP iniciado en {self.host}:{self.port}")
            print(f"📡 Esperando conexiones de equipos GPS...")
            
            while self.running:
                try:
                    # Aceptar nueva conexión
                    client_socket, client_address = self.server_socket.accept()
                    
                    # Log de nueva conexión
                    self.receptor_logger.log_connection(client_address, "CONECTADO")
                    
                    # Crear hilo para manejar la conexión
                    client_thread = threading.Thread(
                        target=self.handle_client,
                        args=(client_socket, client_address)
                    )
                    client_thread.daemon = True
                    client_thread.start()
                    
                except socket.error as e:
                    if self.running:
                        logger.error(f"Error aceptando conexión: {e}")
                        # Si el socket fue cerrado, salir del loop
                        if "Bad file descriptor" in str(e) or "Socket operation on non-socket" in str(e):
                            break
                        
        except Exception as e:
            error_occurred = True
            logger.error(f"Error iniciando servidor TCP: {e}")
            print(f"❌ Error iniciando servidor TCP: {e}")
            import traceback
            logger.error(traceback.format_exc())
        finally:
            # Solo actualizar BD si hubo un error, no si se detuvo normalmente
            self.stop(update_db_on_error=error_occurred)
    
    def stop(self, update_db_on_error=False):
        """
        Detener el servidor TCP
        
        Args:
            update_db_on_error: Si es True, actualiza la BD para marcar el receptor como inactivo
        """
        self.running = False
        if self.server_socket:
            try:
                self.server_socket.close()
            except Exception as e:
                logger.warning(f"Error cerrando socket: {e}")
        
        # Log de detención
        self.receptor_logger.log_receptor_status("DETENIDO", f"Puerto {self.port} cerrado")
        
        logger.info("Servidor TCP detenido")
        print("🛑 Servidor TCP detenido")
        
        # Si se detuvo por un error, actualizar la BD para evitar auto-reinicio
        if update_db_on_error:
            try:
                from gps.models import ConfiguracionReceptor
                config = ConfiguracionReceptor.objects.get(puerto=self.port)
                if config.activo:
                    config.activo = False
                    config.save()
                    logger.info(f"Receptor en puerto {self.port} marcado como inactivo en BD debido a error")
            except Exception as e:
                logger.warning(f"No se pudo actualizar estado en BD para puerto {self.port}: {e}")
    
    def handle_client(self, client_socket: socket.socket, client_address):
        """
        Manejar conexión de un cliente.
        
        Args:
            client_socket: Socket del cliente
            client_address: Tupla (ip, puerto) del cliente
        """
        client_id = f"{client_address[0]}:{client_address[1]}"
        self.clients[client_id] = client_socket
        self.stats['total_connections'] += 1
        
        logger.info(f"🔗 Nueva conexión desde {client_id}")
        print(f"🔗 Nueva conexión desde {client_id}")
        
        try:
            while self.running:
                # Recibir datos del cliente
                data = client_socket.recv(1024)
                if not data:
                    break
                
                # Convertir datos a hexadecimal para logging
                hex_data = data.hex()
                
                # Log de datos recibidos
                self.receptor_logger.log_data_received(client_address, len(data), hex_data)
                
                # Procesar el mensaje
                self.process_message(data, client_id)
                
        except Exception as e:
            logger.error(f"Error manejando cliente {client_id}: {e}")
            print(f"❌ Error con cliente {client_id}: {e}")
            
        finally:
            # Limpiar conexión
            client_socket.close()
            if client_id in self.clients:
                del self.clients[client_id]
            logger.info(f"🔌 Conexión cerrada: {client_id}")
            print(f"🔌 Conexión cerrada: {client_id}")
    
    def process_message(self, data: bytes, client_id: str):
        """
        Procesar mensaje recibido de un equipo GPS.
        
        Args:
            data: Datos crudos recibidos
            client_id: ID del cliente que envió el mensaje
        """
        try:
            self.stats['total_messages'] += 1
            
            logger.info(f"📨 Mensaje recibido de {client_id} ({len(data)} bytes)")
            
            # Parsear datos usando el procesador
            parsed_data = self.processor.parse(data)
            
            if parsed_data:
                self.stats['successful_parses'] += 1
                
                # Log de datos parseados exitosamente
                self.receptor_logger.log_parsed_data(parsed_data)
                
                logger.info(f"✅ Datos parseados: {parsed_data}")
                
                # Guardar en base de datos
                success = self.save_to_database(parsed_data)
                
                if success:
                    print(f"💾 Posición guardada: {parsed_data.get('latitud'):.6f}, "
                          f"{parsed_data.get('longitud'):.6f}")
                else:
                    print(f"⚠️  Posición no guardada (equipo no encontrado o error)")
            else:
                self.stats['failed_parses'] += 1
                
                # Log de error de parsing
                self.receptor_logger.log_warning(f"No se pudo parsear el mensaje desde {client_id}")
                
                logger.warning(f"⚠️  No se pudo parsear el mensaje de {client_id}")
                print(f"⚠️  No se pudo parsear el mensaje")
                
        except Exception as e:
            logger.error(f"Error procesando mensaje de {client_id}: {e}")
            print(f"❌ Error procesando mensaje: {e}")
    
    def save_to_database(self, parsed_data: Dict) -> bool:
        """
        Guardar datos parseados en la base de datos.
        
        Args:
            parsed_data: Diccionario con datos parseados
        
        Returns:
            True si se guardó exitosamente, False en caso contrario
        """
        try:
            # Extraer datos
            device_id = parsed_data.get('device_id') or parsed_data.get('imei')
            latitud = parsed_data.get('latitud')
            longitud = parsed_data.get('longitud')
            velocidad = parsed_data.get('velocidad', 0)
            rumbo = parsed_data.get('rumbo', 0)
            timestamp = parsed_data.get('timestamp')
            
            if not device_id:
                logger.error("No se pudo obtener device_id del mensaje")
                return False
            
            # Buscar el móvil por gps_id
            try:
                movil = Movil.objects.get(gps_id=device_id)
            except Movil.DoesNotExist:
                logger.warning(f"Equipo GPS con ID {device_id} no encontrado en la base de datos")
                print(f"⚠️  Equipo {device_id} no está registrado en la base de datos")
                return False
            
            # Usar ID de empresa directamente (default: 1)
            # La tabla empresas no existe, así que usamos el ID directamente
            empresa_id = 1
            
            # Parsear timestamp si es string
            if isinstance(timestamp, str):
                try:
                    fecha_gps = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                except:
                    fecha_gps = timezone.now()
            else:
                fecha_gps = timestamp or timezone.now()
            
            # Crear registro en Posicion
            posicion = Posicion.objects.create(
                empresa_id=empresa_id,
                movil=movil,
                device_id=device_id,
                fec_gps=fecha_gps,
                fec_report=timezone.now(),
                lat=latitud,
                lon=longitud,
                velocidad=velocidad,
                rumbo=rumbo,
                altitud=parsed_data.get('altitud', 0),
                sats=parsed_data.get('satelites', 0),
                ign_on=parsed_data.get('ignicion', False),
                is_valid=True,
                protocol='TQ',
                provider='Queclink'
            )
            
            # Actualizar MovilStatus
            MovilStatus.objects.update_or_create(
                movil=movil,
                defaults={
                    'ultimo_lat': latitud,
                    'ultimo_lon': longitud,
                    'ultima_altitud': parsed_data.get('altitud', 0),
                    'ultima_velocidad_kmh': velocidad,
                    'ultimo_rumbo': rumbo,
                    'satelites': parsed_data.get('satelites', 0),
                    'ignicion': parsed_data.get('ignicion', False),
                                        'fecha_gps': fecha_gps,
                    'fecha_recepcion': timezone.now(),
                    'id_ultima_posicion': posicion.id,
                    'estado_conexion': 'conectado'
                }
            )
            
            # Geocodificar la posición
            try:
                geocoding_service = GeocodingService()
                resultado_geocode = geocoding_service.geocodificar_coordenadas(latitud, longitud)
                
                if resultado_geocode:
                    direccion_formateada = resultado_geocode.get('direccion_formateada') or \
                                          resultado_geocode.get('display_name', '')
                    
                    # Actualizar Posicion con dirección geocodificada
                    posicion.direccion = direccion_formateada
                    posicion.save()
                    
                    # Actualizar MovilGeocode
                    MovilGeocode.objects.update_or_create(
                        movil=movil,
                        defaults={
                            'direccion_formateada': direccion_formateada,
                            'calle': resultado_geocode.get('calle'),
                            'numero': resultado_geocode.get('numero'),
                            'localidad': resultado_geocode.get('localidad'),
                            'provincia': resultado_geocode.get('provincia'),
                            'pais': resultado_geocode.get('pais'),
                            'fuente_geocodificacion': resultado_geocode.get('fuente_geocodificacion'),
                            'confianza_geocodificacion': resultado_geocode.get('confianza_geocodificacion'),
                            'geohash': resultado_geocode.get('geohash'),
                            'fecha_geocodificacion': timezone.now()
                        }
                    )
            except Exception as e:
                logger.warning(f"Error en geocodificación: {e}")
            
            # Actualizar estadísticas de recepción
            self.update_statistics(movil.id)
            
            logger.info(f"✅ Posición guardada para móvil {movil.patente}")
            return True
            
        except Exception as e:
            self.stats['database_errors'] += 1
            logger.error(f"Error guardando en base de datos: {e}")
            return False
    
    def update_statistics(self, movil_id: int):
        """
        Actualizar estadísticas de recepción.
        
        Args:
            movil_id: ID del móvil que envió datos
        """
        try:
            from django.db.models import F, Count
            
            # Obtener configuración de receptor (debería existir ya que se registró en __init__)
            try:
                receptor = ConfiguracionReceptor.objects.get(puerto=self.port)
            except ConfiguracionReceptor.DoesNotExist:
                # Si no existe, crearla (fallback)
                receptor = ConfiguracionReceptor.objects.create(
                    puerto=self.port,
                    nombre=f'Receptor TCP Puerto {self.port}',
                    protocolo=self.protocolo,
                    activo=True,
                    max_conexiones=100,
                    max_equipos=1000,
                    timeout=30,
                    tipo_equipo_id=1
                )
            
            # Obtener o crear estadísticas para hoy
            hoy = timezone.now().date()
            
            # Contar equipos únicos conectados hoy
            equipos_conectados_count = Posicion.objects.filter(
                fec_gps__date=hoy,
                movil__gps_id__isnull=False
            ).values('movil_id').distinct().count()
            
            # Obtener o crear estadísticas
            stats, created = EstadisticasRecepcion.objects.get_or_create(
                receptor=receptor,
                fecha=hoy,
                defaults={
                    'equipos_conectados': equipos_conectados_count,
                    'datos_recibidos': 1,
                    'datos_procesados': 1,
                    'errores': 0
                }
            )
            
            if not created:
                # Incrementar contadores si ya existe
                # Y actualizar contador de equipos conectados
                estadisticas_hoy = EstadisticasRecepcion.objects.filter(id=stats.id)
                estadisticas_hoy.update(
                    datos_recibidos=F('datos_recibidos') + 1,
                    datos_procesados=F('datos_procesados') + 1,
                    equipos_conectados=equipos_conectados_count
                )
            
        except Exception as e:
            # No fallar si hay error en estadísticas
            logger.warning(f"Error actualizando estadísticas: {e}")
    
    def get_stats(self) -> Dict:
        """
        Obtener estadísticas del receptor.
        
        Returns:
            Diccionario con estadísticas
        """
        return {
            **self.stats,
            'running': self.running,
            'host': self.host,
            'port': self.port,
            'active_connections': len(self.clients),
            'clients': list(self.clients.keys())
        }
    
    def print_stats(self):
        """Imprimir estadísticas en consola"""
        stats = self.get_stats()
        print("\n📊 ESTADÍSTICAS DEL RECEPTOR")
        print("-" * 40)
        print(f"Estado: {'🟢 Ejecutándose' if stats['running'] else '🔴 Detenido'}")
        print(f"Host: {stats['host']}")
        print(f"Puerto: {stats['port']}")
        print(f"Conexiones totales: {stats['total_connections']}")
        print(f"Conexiones activas: {stats['active_connections']}")
        print(f"Mensajes totales: {stats['total_messages']}")
        print(f"Parseos exitosos: {stats['successful_parses']}")
        print(f"Parseos fallidos: {stats['failed_parses']}")
        print(f"Errores de BD: {stats['database_errors']}")
        print("-" * 40)


def main():
    """Función principal para ejecutar el receptor TCP"""
    import sys
    
    print("=" * 60)
    print("🚀 RECEPTOR TCP PARA EQUIPOS GPS - WAYGPS")
    print("=" * 60)
    
    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Crear y configurar receptor
    receiver = TCPReceiver(host='0.0.0.0', port=5003)
    
    try:
        # Iniciar receptor (bloquea hasta detenerse)
        receiver.start()
    except KeyboardInterrupt:
        print("\n🛑 Interrupción detectada...")
    finally:
        receiver.stop()
        print("\n📊 Estadísticas finales:")
        receiver.print_stats()
        print("👋 Receptor TCP cerrado correctamente")


if __name__ == "__main__":
    # Ejecutar receptor
    main()
