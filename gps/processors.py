"""
Procesadores de datos GPS
==========================

Este archivo contiene los parsers para interpretar datos crudos de equipos GPS
según el protocolo específico de cada fabricante (Teltonika, Queclink, etc.).

INSTRUCCIONES PARA INTEGRAR TU CÓDIGO:
---------------------------------------
1. Reemplaza las implementaciones de ejemplo en las clases por tu código real
2. Mantén la interfaz pública (nombres de métodos) para compatibilidad
3. Asegúrate de que devuelvan el formato estandarizado especificado

ESTRUCTURA:
-----------
- BaseProcessor: Clase base abstracta
- TeltonikaProcessor: Procesador para equipos Teltonika
- QueclinkProcessor: Procesador para equipos Queclink (incluir TU CÓDIGO AQUÍ)
- GenericProcessor: Procesador genérico para protocolos desconocidos
"""

import logging
import binascii
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime, timedelta, timezone as dt_timezone
from django.utils import timezone as django_timezone
try:
    from zoneinfo import ZoneInfo
    ZONEINFO_AVAILABLE = True
except ImportError:
    # Fallback para Python < 3.9
    try:
        from backports.zoneinfo import ZoneInfo
        ZONEINFO_AVAILABLE = True
    except ImportError:
        ZONEINFO_AVAILABLE = False

logger = logging.getLogger(__name__)


class BaseProcessor(ABC):
    """Clase base abstracta para todos los procesadores GPS"""
    
    @abstractmethod
    def parse(self, raw_data: bytes, imei: str = None) -> Optional[Dict[str, Any]]:
        """
        Parsear datos crudos del equipo GPS.
        
        Args:
            raw_data: Datos crudos recibidos
            imei: IMEI del equipo (opcional)
        
        Returns:
            Diccionario con datos parseados en formato estándar o None si hay error
        """
        pass
    
    def validate_coordinates(self, lat: float, lon: float) -> bool:
        """Validar que las coordenadas estén en un rango válido"""
        return -90 <= lat <= 90 and -180 <= lon <= 180
    
    def validate_imei(self, imei: str) -> bool:
        """Validar formato de IMEI (15 dígitos)"""
        if not imei:
            return False
        return imei.isdigit() and len(imei) == 15
    
    def format_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Formatear respuesta en formato estándar.
        
        Este método asegura que todos los procesadores devuelvan el mismo formato.
        """
        return {
            'imei': data.get('imei'),
            'timestamp': data.get('timestamp', datetime.now().isoformat()),
            'latitud': data.get('latitud'),
            'longitud': data.get('longitud'),
            'altitud': data.get('altitud'),
            'velocidad': data.get('velocidad'),
            'rumbo': data.get('rumbo'),
            'satelites': data.get('satelites'),
            'ignicion': data.get('ignicion', False),
            'bateria': data.get('bateria'),
            'odometro': data.get('odometro'),
            'quality': data.get('quality', 'good'),
            'raw_data': data.get('raw_data')
        }
    
    def get_id_ok(self, hex_data: str) -> str:
        """
        Extraer ID del equipo desde datos hexadecimales.
        Según el protocolo TQ: ID completo en posiciones 2-12 (10 dígitos), 
        para usar solo los últimos 5 dígitos.
        """
        try:
            id_completo = hex_data[2:12]  # Posiciones 2-11 (10 dígitos)
            if len(id_completo) == 10:
                return id_completo[-5:]  # Últimos 5 dígitos
            return id_completo.zfill(5)
        except:
            return "00000"
    
    def get_lat_chino(self, hex_data: str) -> float:
        """
        Extraer latitud del protocolo TQ (posiciones 24-33).
        Formato: GGMM.MMMMMM (grados, minutos, decimales de minutos).
        """
        try:
            valor = hex_data[24:34]  # Posiciones 24-33 (10 dígitos)
            grados = int(valor[0:2])
            minutos_enteros = int(valor[2:4])
            decimales_minutos = int(valor[4:10]) / 1000000.0
            
            minutos_completos = minutos_enteros + decimales_minutos
            latitud = grados + (minutos_completos / 60.0)
            return round(-latitud, 7)  # Negativo para hemisferio sur
        except:
            return 0.0
    
    def get_lon_chino(self, hex_data: str) -> float:
        """
        Extraer longitud del protocolo TQ (posiciones 34-43).
        Formato: GGGMM.MMMMMM (grados, minutos, decimales de minutos).
        """
        try:
            valor = hex_data[34:44]  # Posiciones 34-43 (10 dígitos)
            grados = int(valor[0:3])
            minutos_enteros = int(valor[3:5])
            decimales_minutos = int(valor[5:10]) / 100000.0
            
            minutos_completos = minutos_enteros + decimales_minutos
            longitud = grados + (minutos_completos / 60.0)
            return round(-longitud, 7)  # Negativo para hemisferio oeste
        except:
            return 0.0
    
    def get_vel_chino(self, hex_data: str) -> int:
        """Extraer velocidad del protocolo TQ (en nudos/knots, posiciones 44-46)"""
        try:
            if len(hex_data) >= 50:
                vel_str = hex_data[44:47]
                vel_decimal = int(vel_str)
                if 0 <= vel_decimal <= 255:
                    return vel_decimal
            return 0
        except:
            return 0
    
    def get_rumbo_chino(self, hex_data: str) -> int:
        """Extraer rumbo del protocolo TQ (en grados 0-360, posiciones 47-49)"""
        try:
            if len(hex_data) >= 50:
                rumbo_str = hex_data[47:50]
                rumbo_decimal = int(rumbo_str)
                if 0 <= rumbo_decimal <= 360:
                    return rumbo_decimal
            return 0
        except:
            return 0
    
    def get_fecha_gps_tq(self, hex_data: str) -> str:
        """Extraer fecha GPS del protocolo TQ (posiciones 18-23, formato DDMMYY)"""
        try:
            valor = hex_data[18:24]
            return f"{valor[0:2]}/{valor[2:4]}/{valor[4:6]}"
        except:
            return ""
    
    def get_hora_gps_tq(self, hex_data: str) -> str:
        """Extraer hora GPS del protocolo TQ (posiciones 12-17, formato HHMMSS)"""
        try:
            valor = hex_data[12:18]
            return f"{valor[0:2]}:{valor[2:4]}:{valor[4:6]}"
        except:
            return ""


class TeltonikaProcessor(BaseProcessor):
    """
    Procesador para equipos Teltonika.
    
    Implementar el parsing según el protocolo Teltonika Codec 8/Codec 8 Extended.
    """
    
    def parse(self, raw_data: bytes, imei: str = None) -> Optional[Dict[str, Any]]:
        """
        Parsear datos Teltonika.
        
        TODO: Implementar tu lógica de parsing aquí o reemplazar con tu código.
        """
        try:
            logger.info(f"Parseando datos Teltonika - IMEI: {imei}, Bytes: {len(raw_data)}")
            
            # ================================================================
            # AQUÍ VA TU CÓDIGO DE PARSING DE TELTONIKA
            # ================================================================
            
            parsed_data = {
                'imei': imei,
                'timestamp': datetime.now().isoformat(),
                'latitud': 0.0,
                'longitud': 0.0,
                'altitud': 0,
                'velocidad': 0,
                'rumbo': 0,
                'satelites': 0,
                'ignicion': False,
                'bateria': None,
                'raw_data': raw_data.hex() if raw_data else None
            }
            
            return self.format_response(parsed_data)
            
        except Exception as e:
            logger.error(f"Error parseando datos Teltonika: {e}", exc_info=True)
            return None


class QueclinkProcessor(BaseProcessor):
    """
    Procesador para equipos Queclink (TQ).
    
    Implementa el parsing del protocolo TQ usando la lógica extraída de
    tq_server_rpg.py, funciones.py y protocolo.py
    """
    
    def parse(self, raw_data: bytes, imei: str = None) -> Optional[Dict[str, Any]]:
        """
        Parsear datos Queclink (protocolo TQ).
        
        Este método implementa el parsing del protocolo TQ basado en el código
        existente en tq_server_rpg.py
        """
        try:
            logger.info(f"Parseando datos Queclink - Bytes: {len(raw_data)}")
            
            # Convertir datos binarios a hexadecimal
            hex_str = binascii.hexlify(raw_data).decode('ascii')
            logger.debug(f"Datos hexadecimales: {hex_str}")
            
            # Extraer device_id (últimos 5 dígitos del ID completo)
            device_id = self.get_id_ok(hex_str)
            
            # Si no se proporcionó imei, usar el device_id extraído
            if not imei:
                imei = device_id
            
            # Extraer fecha y hora GPS del protocolo TQ
            fecha_gps = self.get_fecha_gps_tq(hex_str)
            hora_gps = self.get_hora_gps_tq(hex_str)
            
            # Construir timestamp si hay fecha/hora GPS
            timestamp = datetime.now().isoformat()
            if fecha_gps and hora_gps:
                try:
                    dia, mes, año = fecha_gps.split('/')
                    hora, minuto, segundo = hora_gps.split(':')
                    # Crear datetime con la hora GPS (asumimos UTC)
                    fecha_gps_dt = datetime(int('20' + año), int(mes), int(dia), 
                                           int(hora), int(minuto), int(segundo))
                    # Log de fecha/hora GPS original (UTC)
                    logger.info(f"🕐 [GPS] Fecha/Hora GPS original (UTC): {fecha_gps} {hora_gps}")
                    
                    # Ajustar a hora local de Argentina (UTC-3): restar 3 horas
                    fecha_gps_local = fecha_gps_dt - timedelta(hours=3)
                    
                    # Marcar explícitamente como timezone de Argentina (UTC-3)
                    # Esto evita que Django lo interprete como UTC
                    if ZONEINFO_AVAILABLE:
                        tz_argentina = ZoneInfo('America/Argentina/Buenos_Aires')
                        fecha_gps_local = fecha_gps_local.replace(tzinfo=tz_argentina)
                    else:
                        # Fallback: usar timezone fijo UTC-3
                        tz_argentina = dt_timezone(timedelta(hours=-3))
                        fecha_gps_local = fecha_gps_local.replace(tzinfo=tz_argentina)
                    
                    timestamp = fecha_gps_local.isoformat()
                    
                    # Log de fecha/hora GPS ajustada (Argentina UTC-3)
                    logger.info(f"🕐 [GPS] Fecha/Hora GPS ajustada (Argentina UTC-3): {fecha_gps_local.strftime('%d/%m/%Y %H:%M:%S')}")
                except Exception as e:
                    logger.warning(f"⚠️ Error procesando fecha/hora GPS: {e}")
                    import traceback
                    logger.warning(traceback.format_exc())
                    pass
            
            # Extraer coordenadas
            latitud = self.get_lat_chino(hex_str)
            longitud = self.get_lon_chino(hex_str)
            
            # Validar coordenadas
            if not self.validate_coordinates(latitud, longitud):
                logger.warning(f"Coordenadas inválidas: lat={latitud}, lon={longitud}")
                latitud = longitud = 0.0
            
            # Extraer velocidad (en nudos) y convertir a km/h
            speed_knots = self.get_vel_chino(hex_str)
            velocidad = speed_knots * 1.852  # Convertir nudos a km/h
            
            # Extraer rumbo
            rumbo = self.get_rumbo_chino(hex_str)
            
            # Construir diccionario de datos parseados
            parsed_data = {
                'imei': imei,
                'device_id': device_id,
                'timestamp': timestamp,
                'fecha_gps': fecha_gps,
                'hora_gps': hora_gps,
                'latitud': latitud,
                'longitud': longitud,
                'altitud': 0,  # No disponible en protocolo TQ
                'velocidad': int(velocidad),
                'rumbo': rumbo,
                'satelites': 0,  # No disponible en protocolo TQ
                'ignicion': False,  # No disponible en protocolo TQ
                'bateria': None,  # No disponible en protocolo TQ
                'quality': 'good' if abs(latitud) > 0.000001 else 'no_fix',
                'raw_data': hex_str
            }
            
            logger.info(f"Datos parseados: lat={latitud:.6f}, lon={longitud:.6f}, "
                       f"vel={velocidad:.1f} km/h, rumbo={rumbo}°")
            
            return self.format_response(parsed_data)
            
        except Exception as e:
            logger.error(f"Error parseando datos Queclink: {e}", exc_info=True)
            return None


class GenericProcessor(BaseProcessor):
    """
    Procesador genérico para protocolos desconocidos.
    
    Intenta parsear datos en formatos comunes (key=value, NMEA, etc.)
    """
    
    def parse(self, raw_data: bytes, imei: str = None) -> Optional[Dict[str, Any]]:
        """
        Parsear datos genéricos.
        
        Intenta detectar el formato automáticamente y parsear.
        """
        try:
            logger.info(f"Parseando datos genéricos - IMEI: {imei}, Bytes: {len(raw_data)}")
            
            # Intentar convertir a string
            try:
                data_str = raw_data.decode('utf-8').strip()
            except:
                logger.warning("No se pudo decodificar como UTF-8")
                return None
            
            # Intentar formato key=value&key2=value2
            if '=' in data_str:
                parsed_data = self.parse_key_value(data_str)
                parsed_data['imei'] = imei
                parsed_data['raw_data'] = raw_data.hex()
                return self.format_response(parsed_data)
            
            # Intentar formato NMEA
            if data_str.startswith('$'):
                parsed_data = self.parse_nmea(data_str)
                parsed_data['imei'] = imei
                parsed_data['raw_data'] = raw_data.hex()
                return self.format_response(parsed_data)
            
            logger.warning(f"Formato desconocido: {data_str[:100]}")
            return None
            
        except Exception as e:
            logger.error(f"Error parseando datos genéricos: {e}", exc_info=True)
            return None
    
    def parse_key_value(self, data_str: str) -> Dict[str, Any]:
        """Parsear formato key=value&key2=value2"""
        parsed = {}
        
        for part in data_str.split('&'):
            if '=' in part:
                key, value = part.split('=', 1)
                key = key.strip().lower()
                value = value.strip()
                
                if 'lat' in key:
                    parsed['latitud'] = float(value)
                elif 'lon' in key or 'lng' in key:
                    parsed['longitud'] = float(value)
                elif 'speed' in key or 'vel' in key:
                    parsed['velocidad'] = float(value)
                elif 'heading' in key or 'cog' in key:
                    parsed['rumbo'] = float(value)
                elif 'alt' in key:
                    parsed['altitud'] = float(value)
                elif 'sats' in key or 'satellites' in key:
                    parsed['satelites'] = int(value)
                elif 'ign' in key or 'ignition' in key:
                    parsed['ignicion'] = value.lower() in ('1', 'true', 'on', 'yes')
                elif 'bat' in key or 'battery' in key:
                    try:
                        parsed['bateria'] = float(value)
                    except:
                        pass
        
        return parsed
    
    def parse_nmea(self, data_str: str) -> Dict[str, Any]:
        """Parsear formato NMEA (ej: $GPRMC)"""
        logger.warning("Parser NMEA no implementado completamente")
        return {
            'timestamp': datetime.now().isoformat(),
            'latitud': 0.0,
            'longitud': 0.0,
        }


class ProcessorFactory:
    """
    Factory para obtener el procesador correcto según el tipo de equipo.
    """
    
    PROCESSORS = {
        'teltonika': TeltonikaProcessor,
        'queclink': QueclinkProcessor,
        'tq': QueclinkProcessor,  # Alias para Queclink
        'generic': GenericProcessor,
    }
    
    @classmethod
    def get_processor(cls, device_type: str) -> BaseProcessor:
        """
        Obtener el procesador para el tipo de equipo especificado.
        
        Args:
            device_type: Tipo de equipo ('teltonika', 'queclink', 'generic')
        
        Returns:
            Instancia del procesador apropiado
        """
        processor_class = cls.PROCESSORS.get(device_type.lower(), GenericProcessor)
        return processor_class()
    
    @classmethod
    def register_processor(cls, device_type: str, processor_class: type):
        """
        Registrar un nuevo procesador personalizado.
        
        Args:
            device_type: Nombre del tipo de equipo
            processor_class: Clase del procesador (debe heredar de BaseProcessor)
        """
        cls.PROCESSORS[device_type.lower()] = processor_class
        logger.info(f"Procesador registrado: {device_type} -> {processor_class.__name__}")


# =========================================================================
# NOTAS PARA INTEGRACIÓN:
# =========================================================================
#
# 1. Clase BaseProcessor: Define la interfaz común
#    - Método parse() debe devolver Dict[str, Any] o None
#    - Formato estándar de respuesta definido en format_response()
#    - Métodos auxiliares para parsing TQ agregados a la clase base
#
# 2. Clases específicas: Implementar parse() con tu lógica
#    - TeltonikaProcessor: Para equipos Teltonika
#    - QueclinkProcessor: Para equipos Queclink (IMPLEMENTADO con código TQ)
#
# 3. Uso del procesador:
#    - processor = ProcessorFactory.get_processor('queclink')
#    - result = processor.parse(raw_data, imei='123456789')
#
# 4. Formato de respuesta esperado:
#    {
#        'imei': '123456789',
#        'timestamp': '2025-10-25T12:00:00',
#        'latitud': -34.603722,
#        'longitud': -58.381592,
#        'altitud': 50,
#        'velocidad': 45.5,
#        'rumbo': 180,
#        'satelites': 8,
#        'ignicion': True,
#        'bateria': 95.5,
#        'quality': 'good'
#    }
#
# =========================================================================
