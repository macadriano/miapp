"""
Servicios para GPS - Geocodificación automática
"""

import requests
import time
from django.utils import timezone
from django.db import transaction
from typing import Optional, Dict, Any

class GeocodingService:
    """
    Servicio para geocodificación automática usando OpenStreetMap Nominatim
    """
    
    def __init__(self):
        self.base_url = "https://nominatim.openstreetmap.org/reverse"
        self.headers = {
            'User-Agent': 'WayGPS/1.0 (contact@waygps.com)'
        }
        self.rate_limit_delay = 1  # 1 segundo entre llamadas
    
    def geocodificar_coordenadas(self, lat: float, lon: float) -> Optional[Dict[str, Any]]:
        """
        Geocodificar coordenadas usando OpenStreetMap Nominatim API
        
        Args:
            lat: Latitud
            lon: Longitud
            
        Returns:
            Diccionario con datos de geocodificación o None si hay error
        """
        try:
            # Parámetros para la consulta
            params = {
                'format': 'json',
                'lat': lat,
                'lon': lon,
                'zoom': 18,
                'addressdetails': 1,
                'accept-language': 'es'
            }
            
            print(f"Geocodificando coordenadas: {lat}, {lon}")
            
            # Hacer la consulta a la API
            response = requests.get(
                self.base_url, 
                params=params, 
                headers=self.headers, 
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if 'address' in data:
                    address = data['address']
                    
                    # Extraer componentes de la dirección
                    direccion_formateada = data.get('display_name', '')
                    
                    # Componentes específicos
                    calle = address.get('road') or address.get('street') or address.get('pedestrian')
                    numero = address.get('house_number')
                    piso = address.get('level')
                    depto = address.get('unit')
                    barrio = address.get('suburb') or address.get('neighbourhood')
                    localidad = address.get('city') or address.get('town') or address.get('village')
                    municipio = address.get('municipality') or address.get('county')
                    provincia = address.get('state')
                    codigo_postal = address.get('postcode')
                    pais = address.get('country')
                    
                    # Metadatos
                    fuente_geocodificacion = 'OpenStreetMap Nominatim'
                    confianza_geocodificacion = 0.8  # Asumimos buena confianza para OSM
                    
                    # Calcular geohash simple (truncado para el campo)
                    geohash = f"{lat:.2f},{lon:.2f}"
                    
                    return {
                        'direccion_formateada': direccion_formateada,
                        'calle': calle,
                        'numero': numero,
                        'piso': piso,
                        'depto': depto,
                        'barrio': barrio,
                        'localidad': localidad,
                        'municipio': municipio,
                        'provincia': provincia,
                        'codigo_postal': codigo_postal,
                        'pais': pais or 'Argentina',
                        'fuente_geocodificacion': fuente_geocodificacion,
                        'confianza_geocodificacion': confianza_geocodificacion,
                        'geohash': geohash,
                        'fecha_geocodificacion': timezone.now()
                    }
                else:
                    print(f"No se encontró información de dirección para {lat}, {lon}")
                    return None
            else:
                print(f"Error en geocodificación: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"Error en geocodificación: {e}")
            return None
    
    def actualizar_geocodificacion_movil(self, movil_id: int) -> bool:
        """
        Actualizar geocodificación para un móvil específico
        
        Args:
            movil_id: ID del móvil
            
        Returns:
            True si se actualizó correctamente, False en caso contrario
        """
        try:
            from moviles.models import Movil, MovilStatus, MovilGeocode
            
            # Buscar el móvil
            movil = Movil.objects.get(id=movil_id)
            status = movil.status
            
            # Verificar si tiene coordenadas válidas
            if not status.ultimo_lat or not status.ultimo_lon:
                print(f"Móvil {movil.patente} no tiene coordenadas válidas")
                return False
            
            lat = float(status.ultimo_lat)
            lon = float(status.ultimo_lon)
            
            # Geocodificar
            geocode_data = self.geocodificar_coordenadas(lat, lon)
            
            if geocode_data:
                # Actualizar o crear geocode
                geocode, created = MovilGeocode.objects.get_or_create(
                    movil=movil,
                    defaults=geocode_data
                )
                
                if not created:
                    # Actualizar datos existentes
                    for key, value in geocode_data.items():
                        setattr(geocode, key, value)
                    geocode.save()
                
                print(f"Geocodificación actualizada para móvil {movil.patente}")
                print(f"  Dirección: {geocode.direccion_formateada}")
                return True
            else:
                print(f"Error en geocodificación para móvil {movil.patente}")
                return False
                
        except Exception as e:
            print(f"Error actualizando geocodificación para móvil {movil_id}: {e}")
            return False
    
    def geocodificar_todos_los_moviles(self) -> int:
        """
        Geocodificar automáticamente todos los móviles que tengan coordenadas
        
        Returns:
            Número de móviles geocodificados exitosamente
        """
        from moviles.models import Movil
        
        moviles_geocodificados = 0
        
        try:
            # Buscar todos los móviles con coordenadas
            moviles_con_coordenadas = Movil.objects.filter(
                status__ultimo_lat__isnull=False,
                status__ultimo_lon__isnull=False
            ).exclude(
                status__ultimo_lat='',
                status__ultimo_lon=''
            )
            
            print(f"Encontrados {moviles_con_coordenadas.count()} móviles con coordenadas")
            
            for movil in moviles_con_coordenadas:
                try:
                    if self.actualizar_geocodificacion_movil(movil.id):
                        moviles_geocodificados += 1
                    
                    # Pausa para no sobrecargar la API
                    time.sleep(self.rate_limit_delay)
                    
                except Exception as e:
                    print(f"Error con móvil {movil.patente}: {e}")
            
            print(f"Geocodificación completada: {moviles_geocodificados} móviles")
            return moviles_geocodificados
            
        except Exception as e:
            print(f"Error en geocodificación masiva: {e}")
            return 0

# Instancia global del servicio
geocoding_service = GeocodingService()
