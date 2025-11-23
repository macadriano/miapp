#!/usr/bin/env python
"""
Script para migrar datos de la estructura actual a la nueva estructura
Basado en la nueva arquitectura propuesta en el Excel
"""

import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wayproject.settings')
django.setup()

from django.db import transaction
from django.utils import timezone
from gps.models import Movil, MovilStatus, MovilGeocode, Posicion, CatMovil, TipoEquipoGPS, ConfiguracionReceptor, EstadisticasRecepcion

def migrar_datos_status():
    """Migrar datos dinámicos a moviles_status"""
    
    print("1. Migrando datos a moviles_status...")
    
    moviles_migrados = 0
    
    for movil in Movil.objects.all():
        try:
            # Crear o actualizar registro en moviles_status
            status, created = MovilStatus.objects.get_or_create(
                movil=movil,
                defaults={
                    'ultimo_lat': movil.ultimo_lat,
                    'ultimo_lon': movil.ultimo_lon,
                    'ultima_altitud': movil.ultima_altitud_m,
                    'ultima_velocidad_kmh': movil.ultima_velocidad_kmh,
                    'ultimo_rumbo': movil.ultimo_rumbo,
                    'satelites': movil.ult_satelites,
                    'hdop': movil.ultimo_hdop,
                    'ignicion': movil.ignicion if movil.ignicion is not None else False,
                    'bateria_pct': movil.bateria_pct,
                    'odometro_km': movil.odometro_km,
                    'fecha_gps': movil.fecha_gps,
                    'fecha_recepcion': movil.fecha_recepcion,
                    'raw_data': movil.raw_data,
                    'raw_json': movil.raw_json,
                }
            )
            
            if created:
                moviles_migrados += 1
                print(f"  Creado status para movil {movil.patente or movil.id}")
            else:
                print(f"  - Status ya existe para movil {movil.patente or movil.id}")
                
        except Exception as e:
            print(f"  Error migrando status de movil {movil.patente or movil.id}: {e}")
    
        print(f"Migrados {moviles_migrados} registros a moviles_status")

def migrar_datos_geocode():
    """Migrar datos de geocodificación a moviles_geocode"""
    
    print("\n2. Migrando datos a moviles_geocode...")
    
    moviles_migrados = 0
    
    for movil in Movil.objects.all():
        try:
            # Crear o actualizar registro en moviles_geocode
            geocode, created = MovilGeocode.objects.get_or_create(
                movil=movil,
                defaults={
                    'direccion_formateada': movil.dir_formateada,
                    'calle': movil.dir_calle,
                    'numero': movil.dir_numero,
                    'piso': movil.dir_piso,
                    'depto': movil.dir_depto,
                    'barrio': movil.dir_barrio,
                    'localidad': movil.dir_localidad,
                    'municipio': movil.dir_municipio,
                    'provincia': movil.dir_provincia,
                    'codigo_postal': movil.dir_cp,
                    'pais': movil.dir_pais or 'Argentina',
                    'fuente_geocodificacion': movil.geo_fuente,
                    'confianza_geocodificacion': movil.geo_confianza,
                    'geohash': movil.geo_geohash,
                    'fecha_geocodificacion': movil.geo_actualizado_at,
                }
            )
            
            if created:
                moviles_migrados += 1
                print(f"  ✓ Creado geocode para móvil {movil.patente or movil.id}")
            else:
                print(f"  - Geocode ya existe para móvil {movil.patente or movil.id}")
                
        except Exception as e:
            print(f"  ❌ Error migrando geocode de móvil {movil.patente or movil.id}: {e}")
    
    print(f"✅ Migrados {moviles_migrados} registros a moviles_geocode")

def migrar_datos_posiciones():
    """Migrar datos a posiciones históricas"""
    
    print("\n3. Migrando datos a posiciones...")
    
    posiciones_creadas = 0
    
    for movil in Movil.objects.all():
        try:
            # Solo crear posición si hay coordenadas válidas
            if movil.ultimo_lat and movil.ultimo_lon:
                posicion = Posicion.objects.create(
                    movil=movil,
                    latitud=movil.ultimo_lat,
                    longitud=movil.ultimo_lon,
                    altitud=movil.ultima_altitud_m,
                    velocidad_kmh=movil.ultima_velocidad_kmh,
                    rumbo=movil.ultimo_rumbo,
                    satelites=movil.ult_satelites,
                    hdop=movil.ultimo_hdop,
                    ignicion=movil.ignicion,
                    bateria_pct=movil.bateria_pct,
                    odometro_km=movil.odometro_km,
                    fecha_gps=movil.fecha_gps or timezone.now(),
                    raw_data=movil.raw_data,
                    raw_json=movil.raw_json,
                )
                
                # Actualizar referencia en moviles_status
                if hasattr(movil, 'status'):
                    movil.status.id_ultima_posicion = posicion.id
                    movil.status.save()
                
                posiciones_creadas += 1
                print(f"  ✓ Creada posición para móvil {movil.patente or movil.id}")
            else:
                print(f"  - Sin coordenadas para móvil {movil.patente or movil.id}")
                
        except Exception as e:
            print(f"  ❌ Error migrando posición de móvil {movil.patente or movil.id}: {e}")
    
    print(f"✅ Creadas {posiciones_creadas} posiciones históricas")

def crear_datos_iniciales():
    """Crear datos iniciales para catálogos y tipos de equipos"""
    
    print("\n4. Creando datos iniciales...")
    
    # Crear catálogos de móviles
    catalogo_moviles = [
        {'codigo': 'AUTO', 'nombre': 'Automóvil', 'descripcion': 'Vehículo de pasajeros', 'orden': 1, 'color_hex': '#007bff'},
        {'codigo': 'CAMION', 'nombre': 'Camión', 'descripcion': 'Vehículo de carga', 'orden': 2, 'color_hex': '#28a745'},
        {'codigo': 'MOTO', 'nombre': 'Motocicleta', 'descripcion': 'Vehículo de dos ruedas', 'orden': 3, 'color_hex': '#ffc107'},
        {'codigo': 'BUS', 'nombre': 'Ómnibus', 'descripcion': 'Vehículo de transporte público', 'orden': 4, 'color_hex': '#dc3545'},
    ]
    
    for cat_data in catalogo_moviles:
        cat, created = CatMovil.objects.get_or_create(
            codigo=cat_data['codigo'],
            defaults=cat_data
        )
        if created:
            print(f"  ✓ Creado catálogo: {cat.nombre}")
        else:
            print(f"  - Catálogo ya existe: {cat.nombre}")
    
    # Crear tipos de equipos GPS
    tipos_equipos = [
        {
            'codigo': 'TELTONIKA',
            'nombre': 'Teltonika FMB',
            'fabricante': 'Teltonika',
            'protocolo': 'TCP',
            'puerto_default': 8080,
            'formato_datos': {
                "codec": "8",
                "fields": ["timestamp", "priority", "lng", "lat", "altitude", "angle", "satellites", "speed"]
            }
        },
        {
            'codigo': 'QUECLINK',
            'nombre': 'Queclink GV300',
            'fabricante': 'Queclink',
            'protocolo': 'TCP',
            'puerto_default': 8081,
            'formato_datos': {
                "format": "queclink",
                "fields": ["imei", "timestamp", "lat", "lng", "speed", "heading"]
            }
        },
        {
            'codigo': 'GENERIC',
            'nombre': 'Genérico',
            'fabricante': 'Varios',
            'protocolo': 'TCP',
            'puerto_default': 8082,
            'formato_datos': {
                "format": "keyvalue",
                "fields": ["imei", "lat", "lon", "speed", "heading"]
            }
        }
    ]
    
    for tipo_data in tipos_equipos:
        tipo, created = TipoEquipoGPS.objects.get_or_create(
            codigo=tipo_data['codigo'],
            defaults=tipo_data
        )
        if created:
            print(f"  ✓ Creado tipo de equipo: {tipo.nombre}")
        else:
            print(f"  - Tipo de equipo ya existe: {tipo.nombre}")
    
    print("✅ Datos iniciales creados")

def verificar_migracion():
    """Verificar que la migración fue exitosa"""
    
    print("\n5. Verificando migración...")
    
    # Contar registros
    total_moviles = Movil.objects.count()
    total_status = MovilStatus.objects.count()
    total_geocode = MovilGeocode.objects.count()
    total_posiciones = Posicion.objects.count()
    total_catalogos = CatMovil.objects.count()
    total_flotas = Flota.objects.count()
    
    print(f"  📊 Estadísticas:")
    print(f"    - Móviles: {total_moviles}")
    print(f"    - Estados: {total_status}")
    print(f"    - Geocodificaciones: {total_geocode}")
    print(f"    - Posiciones: {total_posiciones}")
    print(f"    - Catálogos: {total_catalogos}")
    print(f"    - Flotas: {total_flotas}")
    
    # Verificar relaciones
    moviles_con_status = Movil.objects.filter(status__isnull=False).count()
    moviles_con_geocode = Movil.objects.filter(geocode__isnull=False).count()
    moviles_con_posiciones = Movil.objects.filter(posiciones__isnull=False).count()
    
    print(f"\n  🔗 Relaciones:")
    print(f"    - Móviles con status: {moviles_con_status}/{total_moviles}")
    print(f"    - Móviles con geocode: {moviles_con_geocode}/{total_moviles}")
    print(f"    - Móviles con posiciones: {moviles_con_posiciones}/{total_moviles}")
    
    # Verificar datos de ejemplo
    if total_moviles > 0:
        movil_ejemplo = Movil.objects.first()
        print(f"\n  📋 Ejemplo de móvil migrado:")
        print(f"    - ID: {movil_ejemplo.id}")
        print(f"    - Patente: {movil_ejemplo.patente}")
        print(f"    - Tiene status: {hasattr(movil_ejemplo, 'status')}")
        print(f"    - Tiene geocode: {hasattr(movil_ejemplo, 'geocode')}")
        print(f"    - Posiciones: {movil_ejemplo.posiciones.count()}")
    
    print("\n✅ Verificación completada")

def migrar_estructura_completa():
    """Ejecutar migración completa"""
    
    print("=" * 80)
    print("MIGRACIÓN A NUEVA ESTRUCTURA - WAYGPS")
    print("=" * 80)
    
    try:
        with transaction.atomic():
            # Ejecutar migraciones en orden
            migrar_datos_status()
            migrar_datos_geocode()
            migrar_datos_posiciones()
            crear_datos_iniciales()
            verificar_migracion()
            
        print("\n" + "=" * 80)
        print("✅ MIGRACIÓN COMPLETADA EXITOSAMENTE")
        print("=" * 80)
        print("\nPróximos pasos:")
        print("1. Probar funcionalidad existente")
        print("2. Actualizar código para nueva estructura")
        print("3. Implementar receptores GPS")
        print("4. Implementar WebSockets")
        print("5. Testing completo")
        
    except Exception as e:
        print(f"\n❌ ERROR EN MIGRACIÓN: {e}")
        import traceback
        traceback.print_exc()
        print("\n🔄 La migración se revirtió automáticamente")
        print("   Revisa los errores y vuelve a intentar")

if __name__ == "__main__":
    migrar_estructura_completa()
