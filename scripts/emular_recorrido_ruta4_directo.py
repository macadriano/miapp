#!/usr/bin/env python
"""
Script para emular un recorrido realista por Ruta 4 (Camino de Cintura) - Versión directa
"""

import os
import sys
import django
from datetime import datetime, timedelta
import random
import math
import requests
import json

# Configurar Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wayproject.settings')
django.setup()

from django.db import connection
from django.utils import timezone
from django.db import transaction

def calcular_distancia_haversine(lat1, lon1, lat2, lon2):
    """Calcula la distancia entre dos puntos usando la fórmula de Haversine"""
    R = 6371  # Radio de la Tierra en kilómetros
    
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    return R * c

def calcular_rumbo(lat1, lon1, lat2, lon2):
    """Calcula el rumbo (bearing) en grados entre dos puntos"""
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    
    dlon = lon2_rad - lon1_rad
    
    y = math.sin(dlon) * math.cos(lat2_rad)
    x = math.cos(lat1_rad) * math.sin(lat2_rad) - math.sin(lat1_rad) * math.cos(lat2_rad) * math.cos(dlon)
    
    bearing = math.atan2(y, x)
    bearing = math.degrees(bearing)
    bearing = (bearing + 360) % 360
    
    return round(bearing)

def densificar_ruta(route_coords, intervalo_metros=100):
    """Densifica una ruta agregando puntos intermedios"""
    if len(route_coords) < 2:
        return route_coords
    
    puntos_densificados = []
    
    for i in range(len(route_coords) - 1):
        lon1, lat1 = route_coords[i]
        lon2, lat2 = route_coords[i + 1]
        
        # Calcular distancia entre puntos
        distancia = calcular_distancia_haversine(lat1, lon1, lat2, lon2) * 1000  # en metros
        
        if distancia == 0:
            continue
        
        # Calcular número de puntos intermedios
        num_puntos = max(1, int(distancia / intervalo_metros))
        
        for j in range(num_puntos + 1):
            factor = j / num_puntos
            
            lat_interp = lat1 + factor * (lat2 - lat1)
            lon_interp = lon1 + factor * (lon2 - lon1)
            
            puntos_densificados.append([lon_interp, lat_interp])
    
    return puntos_densificados

def obtener_ruta_osrm_real(origen_lat, origen_lon, destino_lat, destino_lon):
    """Obtiene una ruta real usando OSRM que pase por Ruta 4"""
    try:
        # Usar OSRM para obtener ruta real con más densidad
        osrm_url = "http://router.project-osrm.org/route/v1/driving/"
        coords_str = f"{origen_lon},{origen_lat};{destino_lon},{destino_lat}"
        url = f"{osrm_url}{coords_str}?overview=full&geometries=geojson&steps=true"
        
        print(f"🌐 Solicitando ruta a OSRM...")
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        if data['code'] == 'Ok':
            route_coords = data['routes'][0]['geometry']['coordinates']
            print(f"✅ Ruta obtenida de OSRM: {len(route_coords)} puntos")
            
            # Si hay muy pocos puntos, densificar
            if len(route_coords) < 50:
                print("⚠️  Pocos puntos de OSRM, densificando...")
                route_coords = densificar_ruta(route_coords)
                print(f"✅ Ruta densificada: {len(route_coords)} puntos")
            
            return route_coords
        else:
            print(f"❌ Error OSRM: {data['code']}")
            return None
            
    except Exception as e:
        print(f"❌ Error conectando con OSRM: {e}")
        return None

def generar_puntos_ruta4_directa():
    """Genera puntos usando OSRM para obtener una ruta real"""
    
    # Coordenadas de origen y destino (más precisas)
    origen_lat, origen_lon = -34.7012, -58.5834  # Fitz Roy 6185, Isidro Casanova
    destino_lat, destino_lon = -34.8244, -58.3832  # Italia 1157, Burzaco
    
    print(f"📍 Origen: Fitz Roy 6185, Isidro Casanova ({origen_lat}, {origen_lon})")
    print(f"📍 Destino: Italia 1157, Burzaco ({destino_lat}, {destino_lon})")
    
    # Obtener ruta real de OSRM
    route_coords = obtener_ruta_osrm_real(origen_lat, origen_lon, destino_lat, destino_lon)
    
    if route_coords:
        # Convertir coordenadas de OSRM (lon, lat) a (lat, lon) con descripciones
        puntos_ruta = []
        for i, (lon, lat) in enumerate(route_coords):
            if i == 0:
                descripcion = "Fitz Roy 6185, Isidro Casanova"
                tipo_via = "local"
            elif i == len(route_coords) - 1:
                descripcion = "Italia 1157, Burzaco"
                tipo_via = "local"
            elif i < len(route_coords) * 0.1 or i > len(route_coords) * 0.9:
                # Primer y último 10% del recorrido (calles locales)
                descripcion = f"Punto {i+1} - Calle local"
                tipo_via = "local"
            else:
                # Tramo central (Ruta 4 o vías principales)
                descripcion = f"Punto {i+1} - Ruta 4"
                tipo_via = "ruta4"
            
            puntos_ruta.append((lat, lon, descripcion, tipo_via))
        
        return puntos_ruta
    else:
        # Fallback: usar puntos aproximados si OSRM falla
        print("⚠️  Usando ruta aproximada como fallback...")
        return [
            (-34.7012, -58.5834, "Fitz Roy 6185, Isidro Casanova", "local"),
            (-34.8244, -58.3832, "Italia 1157, Burzaco", "local")
        ]

def interpolar_puntos_ruta4(puntos_ruta, intervalo_metros=150):
    """Interpola puntos entre los puntos clave para mayor densidad"""
    puntos_interpolados = []
    
    for i in range(len(puntos_ruta) - 1):
        lat1, lon1, desc1, tipo1 = puntos_ruta[i]
        lat2, lon2, desc2, tipo2 = puntos_ruta[i + 1]
        
        # Calcular distancia entre puntos
        distancia = calcular_distancia_haversine(lat1, lon1, lat2, lon2) * 1000  # en metros
        
        if distancia == 0:
            continue
        
        # Calcular número de puntos intermedios
        num_puntos = max(1, int(distancia / intervalo_metros))
        
        for j in range(num_puntos + 1):
            factor = j / num_puntos
            
            lat_interp = lat1 + factor * (lat2 - lat1)
            lon_interp = lon1 + factor * (lon2 - lon1)
            
            # Usar descripción del punto de origen para puntos intermedios
            descripcion = desc1 if j < num_puntos else desc2
            tipo_via = tipo1 if j < num_puntos else tipo2
            
            puntos_interpolados.append((lat_interp, lon_interp, descripcion, tipo_via))
    
    return puntos_interpolados

def generar_velocidad_por_tipo_via(tipo_via, distancia_anterior):
    """Genera velocidades realistas según el tipo de vía"""
    
    if tipo_via == "ruta4":
        # En Ruta 4: velocidades altas y constantes
        base_velocidad = random.uniform(70, 95)  # 70-95 km/h en Ruta 4
    elif tipo_via == "local":
        # En calles locales: velocidades variables
        if distancia_anterior < 50:  # Posible semáforo o tráfico
            base_velocidad = random.uniform(0, 15)
        elif distancia_anterior < 200:  # Tráfico lento
            base_velocidad = random.uniform(15, 35)
        else:  # Circulación normal en calles
            base_velocidad = random.uniform(25, 50)
    else:
        base_velocidad = random.uniform(20, 40)
    
    # Agregar variación realista
    variacion = random.uniform(-5, 5)
    velocidad = max(0, base_velocidad + variacion)
    
    return round(velocidad, 1)

def generar_recorrido_ruta4_directo():
    """Genera un recorrido realista por Ruta 4 usando puntos específicos"""
    
    print("🚗 Iniciando emulación de recorrido por Ruta 4 (versión directa)...")
    
    # Obtener puntos de la ruta (sin interpolación para mantener la ruta real)
    puntos_ruta = generar_puntos_ruta4_directa()
    print(f"📍 Puntos de la ruta OSRM: {len(puntos_ruta)}")
    
    # Usar los puntos directamente de OSRM (sin interpolación)
    puntos_interpolados = puntos_ruta
    
    # Calcular distancia total
    distancia_total = 0
    for i in range(len(puntos_interpolados) - 1):
        lat1, lon1, _, _ = puntos_interpolados[i]
        lat2, lon2, _, _ = puntos_interpolados[i + 1]
        distancia_total += calcular_distancia_haversine(lat1, lon1, lat2, lon2)
    
    print(f"📏 Distancia total: {distancia_total:.2f} km")
    print(f"⏱️  Tiempo estimado: {int(distancia_total * 1.1)} minutos")
    
    # Obtener o crear móvil
    with connection.cursor() as cursor:
        cursor.execute("SELECT id, patente, alias FROM moviles WHERE patente = 'ASN773' LIMIT 1")
        movil_data = cursor.fetchone()
        
        if not movil_data:
            print("🚙 Creando móvil de prueba...")
            cursor.execute("""
                INSERT INTO moviles (patente, alias, codigo, marca, modelo, activo, created_at, updated_at)
                VALUES ('ASN773', 'Movil Ruta 4 Directo', 'R4DIR', 'Ford', 'Focus', true, NOW(), NOW())
                RETURNING id, patente, alias
            """)
            movil_data = cursor.fetchone()
        
        movil_id, patente, alias = movil_data
        print(f"🚙 Usando móvil: {patente} - {alias}")
    
    # Usar empresa_id = 1 directamente
    empresa_id = 1
    print(f"🏢 Usando empresa ID: {empresa_id}")
    
    # Limpiar posiciones anteriores
    print("🧹 Limpiando posiciones anteriores...")
    with connection.cursor() as cursor:
        cursor.execute("DELETE FROM posiciones WHERE movil_id = %s", [movil_id])
        posiciones_eliminadas = cursor.rowcount
        print(f"🗑️  Posiciones eliminadas: {posiciones_eliminadas}")
    
    # Generar posiciones
    print("🕐 Iniciando recorrido por Ruta 4...")
    tiempo_actual = timezone.now() - timedelta(hours=1)  # Hace 1 hora
    posiciones_creadas = 0
    
    for i, (lat, lon, descripcion, tipo_via) in enumerate(puntos_interpolados):
        # Calcular velocidad según el tipo de vía
        if i > 0:
            lat_ant, lon_ant, _, _ = puntos_interpolados[i-1]
            distancia_anterior = calcular_distancia_haversine(lat_ant, lon_ant, lat, lon) * 1000
            velocidad = generar_velocidad_por_tipo_via(tipo_via, distancia_anterior)
        else:
            velocidad = 0  # Inicio detenido
        
        # Calcular rumbo
        if i < len(puntos_interpolados) - 1:
            lat_sig, lon_sig, _, _ = puntos_interpolados[i + 1]
            rumbo = calcular_rumbo(lat, lon, lat_sig, lon_sig)
        else:
            rumbo = 0
        
        # Generar datos realistas
        altitud = random.randint(10, 50)
        satelites = random.randint(8, 12)
        hdop = round(random.uniform(0.8, 2.0), 2)
        accuracy = random.randint(3, 10)
        
        # Estado del vehículo
        ignicion = velocidad > 0 or random.random() > 0.05  # 95% de probabilidad de estar encendido
        bateria = random.randint(12000, 14000) if ignicion else random.randint(11000, 13000)
        
        # Tiempo entre posiciones (más realista)
        if velocidad > 0:
            if tipo_via == "ruta4":
                tiempo_entre_posiciones = random.randint(10, 25)  # 10-25 segundos en Ruta 4
            else:
                tiempo_entre_posiciones = random.randint(20, 45)  # 20-45 segundos en calles locales
        else:
            tiempo_entre_posiciones = random.randint(30, 90)  # 30 segundos a 1.5 minutos si está detenido
        
        tiempo_actual += timedelta(seconds=tiempo_entre_posiciones)
        
        # Insertar posición
        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO posiciones (
                    empresa_id, device_id, movil_id, fec_gps, fec_report, evento,
                    velocidad, rumbo, lat, lon, altitud, sats, hdop, accuracy_m,
                    ign_on, batt_mv, ext_pwr_mv, inputs_mask, outputs_mask,
                    msg_uid, seq, provider, protocol, raw_payload,
                    is_valid, is_late, is_duplicate, created_at
                ) VALUES (
                    %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, %s
                )
            """, [
                empresa_id, 1, movil_id, tiempo_actual, tiempo_actual, 'GPS',
                int(velocidad), rumbo, lat, lon, altitud, satelites, hdop, accuracy,
                ignicion, bateria, 0, '00000000', '00000000',
                f'ruta4_{i}_{int(tiempo_actual.timestamp())}', i, 'teltonika', 'FMB920',
                f'raw_data_{i}', True, False, False, tiempo_actual
            ])
        
        posiciones_creadas += 1
        
        # Mostrar progreso cada 15 posiciones
        if i % 15 == 0 or i == len(puntos_interpolados) - 1:
            print(f"📍 Posición {i+1}/{len(puntos_interpolados)}: {lat:.6f}, {lon:.6f} - {velocidad} km/h - {descripcion} ({tipo_via})")
    
    # Actualizar estado del móvil con la última posición
    if puntos_interpolados:
        ultima_lat, ultima_lon, ultima_desc, ultima_tipo = puntos_interpolados[-1]
        
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO moviles_status (movil_id, fec_gps, velocidad, rumbo, ignicion, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, NOW(), NOW())
                    ON CONFLICT (movil_id) DO UPDATE SET
                        fec_gps = EXCLUDED.fec_gps,
                        velocidad = EXCLUDED.velocidad,
                        rumbo = EXCLUDED.rumbo,
                        ignicion = EXCLUDED.ignicion,
                        updated_at = NOW()
                """, [movil_id, tiempo_actual, int(velocidad), rumbo, ignicion])
            
            print(f"✅ Estado del móvil actualizado: {ultima_desc}")
        except Exception as e:
            print(f"⚠️  No se pudo actualizar moviles_status: {e}")
            print(f"📍 Última posición: {ultima_desc} ({ultima_lat:.6f}, {ultima_lon:.6f})")
    
    print(f"\n🎉 Recorrido por Ruta 4 completado!")
    print(f"📊 Estadísticas:")
    print(f"   - Posiciones creadas: {posiciones_creadas}")
    print(f"   - Distancia total: {distancia_total:.2f} km")
    print(f"   - Tiempo total: {int(distancia_total * 1.1)} minutos")
    print(f"   - Velocidad promedio: {distancia_total * 1.1 / (posiciones_creadas * 0.5):.1f} km/h")
    
    return posiciones_creadas

if __name__ == '__main__':
    try:
        posiciones_creadas = generar_recorrido_ruta4_directo()
        print(f"\n✅ Script completado exitosamente. {posiciones_creadas} posiciones creadas.")
    except Exception as e:
        print(f"❌ Error ejecutando el script: {e}")
        import traceback
        traceback.print_exc()
