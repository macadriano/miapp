#!/usr/bin/env python
"""
Script para migrar posición manual y implementar geocodificación automática
"""

import os
import sys
import django
import requests
import time
from datetime import datetime

# Configurar Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wayproject.settings')
django.setup()

from django.db import transaction
from django.utils import timezone
from gps.models import Movil, MovilStatus, MovilGeocode, Posicion

def geocodificar_con_osm(lat, lon):
    """
    Geocodificar coordenadas usando OpenStreetMap Nominatim API
    """
    try:
        # URL de la API de Nominatim (OpenStreetMap)
        url = "https://nominatim.openstreetmap.org/reverse"
        
        # Parámetros para la consulta
        params = {
            'format': 'json',
            'lat': lat,
            'lon': lon,
            'zoom': 18,
            'addressdetails': 1,
            'accept-language': 'es'
        }
        
        # Headers para identificar nuestra aplicación
        headers = {
            'User-Agent': 'WayGPS/1.0 (contact@waygps.com)'
        }
        
        print(f"  Geocodificando coordenadas: {lat}, {lon}")
        
        # Hacer la consulta a la API
        response = requests.get(url, params=params, headers=headers, timeout=10)
        
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
                print(f"  No se encontró información de dirección para {lat}, {lon}")
                return None
        else:
            print(f"  Error en geocodificación: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"  Error en geocodificación: {e}")
        return None

def migrar_posicion_y_geocodificar():
    """
    Migrar posición manual del móvil OVV799 y geocodificar
    """
    
    print("=" * 80)
    print("MIGRACION DE POSICION Y GEOCODIFICACION")
    print("=" * 80)
    
    try:
        with transaction.atomic():
            # Buscar el móvil OVV799
            movil = Movil.objects.get(patente='OVV799')
            print(f"1. Móvil encontrado: {movil.alias} ({movil.patente})")
            
            # Obtener el status del móvil
            status = movil.status
            print(f"2. Status encontrado para móvil {movil.patente}")
            
            # Verificar si tiene coordenadas
            if status.ultimo_lat and status.ultimo_lon:
                lat = float(status.ultimo_lat)
                lon = float(status.ultimo_lon)
                print(f"3. Coordenadas encontradas: {lat}, {lon}")
                
                # Crear posición histórica
                posicion = Posicion.objects.create(
                    movil=movil,
                    latitud=lat,
                    longitud=lon,
                    altitud=status.ultima_altitud,
                    velocidad_kmh=status.ultima_velocidad_kmh,
                    rumbo=status.ultimo_rumbo,
                    satelites=status.satelites,
                    hdop=status.hdop,
                    ignicion=status.ignicion,
                    bateria_pct=status.bateria_pct,
                    odometro_km=status.odometro_km,
                    fecha_gps=status.fecha_gps or timezone.now(),
                    raw_data=status.raw_data,
                    raw_json=status.raw_json,
                    calidad_datos='buena'
                )
                
                # Actualizar referencia en status
                status.id_ultima_posicion = posicion.id
                status.save()
                
                print(f"4. Posición histórica creada: ID {posicion.id}")
                
                # Geocodificar las coordenadas
                print("5. Iniciando geocodificación...")
                geocode_data = geocodificar_con_osm(lat, lon)
                
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
                    
                    print(f"6. Geocodificación completada:")
                    print(f"   - Dirección: {geocode.direccion_formateada}")
                    print(f"   - Localidad: {geocode.localidad}")
                    print(f"   - Provincia: {geocode.provincia}")
                    print(f"   - País: {geocode.pais}")
                else:
                    print("6. Error en geocodificación")
                
                # Verificar resultado
                print("\n7. Verificando migración...")
                
                # Contar posiciones del móvil
                posiciones_count = Posicion.objects.filter(movil=movil).count()
                print(f"   - Posiciones históricas: {posiciones_count}")
                
                # Verificar geocode
                try:
                    geocode = movil.geocode
                    print(f"   - Geocodificación: {'Sí' if geocode.direccion_formateada else 'No'}")
                except MovilGeocode.DoesNotExist:
                    print(f"   - Geocodificación: No existe")
                
                print("\nMigración completada exitosamente")
                
            else:
                print("3. No se encontraron coordenadas en el status")
                
    except Movil.DoesNotExist:
        print("Error: No se encontró el móvil OVV799")
    except Exception as e:
        print(f"Error en migración: {e}")
        import traceback
        traceback.print_exc()

def geocodificar_todos_los_moviles():
    """
    Geocodificar automáticamente todos los móviles que tengan coordenadas
    """
    
    print("\n" + "=" * 80)
    print("GEOCODIFICACION AUTOMATICA DE TODOS LOS MOVILES")
    print("=" * 80)
    
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
                status = movil.status
                lat = float(status.ultimo_lat)
                lon = float(status.ultimo_lon)
                
                print(f"\nGeocodificando móvil {movil.patente} ({lat}, {lon})...")
                
                # Geocodificar
                geocode_data = geocodificar_con_osm(lat, lon)
                
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
                    
                    moviles_geocodificados += 1
                    print(f"  Geocodificado: {geocode.localidad}, {geocode.provincia}")
                else:
                    print(f"  Error en geocodificación")
                
                # Pausa para no sobrecargar la API
                time.sleep(1)
                
            except Exception as e:
                print(f"  Error con móvil {movil.patente}: {e}")
        
        print(f"\nGeocodificación completada: {moviles_geocodificados} móviles")
        
    except Exception as e:
        print(f"Error en geocodificación masiva: {e}")

if __name__ == "__main__":
    # Ejecutar migración de posición específica
    migrar_posicion_y_geocodificar()
    
    # Preguntar si geocodificar todos los móviles
    print("\n" + "=" * 80)
    respuesta = input("¿Desea geocodificar todos los móviles con coordenadas? (s/n): ")
    
    if respuesta.lower() in ['s', 'si', 'sí', 'y', 'yes']:
        geocodificar_todos_los_moviles()
    else:
        print("Geocodificación masiva cancelada")
    
    print("\n" + "=" * 80)
    print("PROCESO COMPLETADO")
    print("=" * 80)
