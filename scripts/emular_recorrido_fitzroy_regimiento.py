#!/usr/bin/env python
"""
Script para emular un recorrido desde Fitz Roy 6185 hasta Av. Regimiento de Patricios 1142
Paso por: Camino de Cintura - Ruta 4 - Autopista Ricchieri - Autopista 25 de Mayo - Autopista al Sur - Av. Suarez - Av. Regimiento de Patricios
"""

import os
import sys
import django
from datetime import datetime, timedelta
import random
import math
import requests

# Configurar Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wayproject.settings')
django.setup()

from django.db import connection

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

def obtener_ruta_osrm(coordenadas_puntos):
    """Obtiene una ruta real usando OSRM con múltiples waypoints"""
    try:
        # Construir cadena de coordenadas para OSRM
        coords_str = ";".join([f"{lon},{lat}" for lat, lon, _ in coordenadas_puntos])
        
        osrm_url = "http://router.project-osrm.org/route/v1/driving/"
        url = f"{osrm_url}{coords_str}?overview=full&geometries=geojson"
        
        print(f"🌐 Solicitando ruta a OSRM...")
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        if data['code'] == 'Ok':
            route_coords = data['routes'][0]['geometry']['coordinates']
            print(f"✅ Ruta obtenida de OSRM: {len(route_coords)} puntos")
            return route_coords
        else:
            print(f"❌ Error OSRM: {data['code']}")
            return None
            
    except Exception as e:
        print(f"❌ Error conectando con OSRM: {e}")
        return None

def generar_puntos_fitzroy_regimiento():
    """Genera puntos de un recorrido desde Fitz Roy hasta Regimiento de Patricios"""
    
    # Puntos de referencia del recorrido
    puntos_clave = [
        (-34.7012, -58.5834, "Fitz Roy 6185, Isidro Casanova (Inicio)"),
        (-34.7150, -58.5750, "Aproximándose a Camino de Cintura"),
        (-34.7280, -58.5650, "Camino de Cintura / Ruta 4"),
        (-34.7450, -58.5450, "Ruta 4 - Continuando"),
        (-34.7620, -58.5250, "Ruta 4 - Cerca de Autopista"),
        (-34.7750, -58.5100, "Empalme Autopista Ricchieri"),
        (-34.7850, -58.4950, "Autopista Ricchieri"),
        (-34.7950, -58.4800, "Ricchieri - Aproximándose a 25 de Mayo"),
        (-34.8030, -58.4650, "Confluencia Ricchieri - 25 de Mayo"),
        (-34.8080, -58.4500, "Autopista 25 de Mayo"),
        (-34.8130, -58.4350, "25 de Mayo - Avanzando"),
        (-34.8180, -58.4200, "25 de Mayo - Cerca de Constitución"),
        (-34.8210, -58.4050, "Bajada Constitución - Autopista al Sur"),
        (-34.8240, -58.3900, "Autopista al Sur"),
        (-34.8260, -58.3780, "Bajada Av. Suarez"),
        (-34.8275, -58.3700, "Av. Suarez"),
        (-34.8285, -58.3650, "Av. Suarez - Continuando"),
        (-34.8290, -58.3600, "Empalme Av. Regimiento de Patricios"),
        (-34.8295, -58.3550, "Av. Regimiento de Patricios - Avanzando"),
        (-34.8300, -58.3500, "Av. Regimiento de Patricios 1142 (Destino)")
    ]
    
    print(f"📍 Puntos clave: {len(puntos_clave)}")
    
    # Intentar obtener ruta real de OSRM
    ruta_osrm = obtener_ruta_osrm(puntos_clave)
    
    if ruta_osrm:
        # Convertir coordenadas de OSRM (lon, lat) a (lat, lon) con descripciones
        puntos_ruta = []
        total_puntos = len(ruta_osrm)
        
        for i, (lon, lat) in enumerate(ruta_osrm):
            # Asignar descripciones basadas en la posición en la ruta
            if i == 0:
                descripcion = "Fitz Roy 6185, Isidro Casanova (Inicio)"
            elif i == total_puntos - 1:
                descripcion = "Av. Regimiento de Patricios 1142 (Destino)"
            elif i < total_puntos * 0.1:
                descripcion = "Aproximándose a Camino de Cintura"
            elif i < total_puntos * 0.25:
                descripcion = "Ruta 4"
            elif i < total_puntos * 0.45:
                descripcion = "Autopista Ricchieri"
            elif i < total_puntos * 0.65:
                descripcion = "Autopista 25 de Mayo"
            elif i < total_puntos * 0.80:
                descripcion = "Autopista al Sur"
            elif i < total_puntos * 0.95:
                descripcion = "Av. Suarez"
            else:
                descripcion = "Av. Regimiento de Patricios"
            
            puntos_ruta.append((lat, lon, descripcion))
        
        return puntos_ruta
    else:
        # Fallback a puntos clave si OSRM falla
        print("⚠️  Usando ruta aproximada como fallback...")
        return puntos_clave

def interpolar_puntos(puntos_ruta, intervalo_metros=80):
    """Interpola puntos entre los puntos clave para mayor densidad"""
    puntos_interpolados = []
    
    for i in range(len(puntos_ruta) - 1):
        lat1, lon1, desc1 = puntos_ruta[i]
        lat2, lon2, desc2 = puntos_ruta[i + 1]
        
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
            
            puntos_interpolados.append((lat_interp, lon_interp, descripcion))
    
    return puntos_interpolados

def generar_velocidad_realista(distancia_anterior, es_autopista=False):
    """Genera velocidades realistas según el tipo de vía"""
    
    if es_autopista:
        # En autopista: velocidades altas (80-110 km/h)
        base_velocidad = random.uniform(80, 110)
    else:
        # En calles locales: velocidades variables
        if distancia_anterior < 50:  # Posible semáforo o tráfico
            base_velocidad = random.uniform(0, 15)
        elif distancia_anterior < 200:  # Tráfico lento
            base_velocidad = random.uniform(15, 40)
        else:  # Circulación normal
            base_velocidad = random.uniform(30, 60)
    
    # Agregar variación realista
    variacion = random.uniform(-10, 10)
    velocidad = max(0, base_velocidad + variacion)
    
    return round(velocidad, 1)

def generar_recorrido_fitzroy_regimiento():
    """Genera un recorrido desde Fitz Roy hasta Regimiento de Patricios"""
    
    print("🚗 Iniciando emulación de recorrido Fitz Roy -> Regimiento de Patricios...")
    
    # Obtener puntos de la ruta
    puntos_ruta = generar_puntos_fitzroy_regimiento()
    print(f"📍 Puntos clave de la ruta: {len(puntos_ruta)}")
    
    # Interpolar puntos para mayor densidad
    puntos_interpolados = interpolar_puntos(puntos_ruta, intervalo_metros=80)
    print(f"📍 Puntos interpolados: {len(puntos_interpolados)}")
    
    # Calcular distancia total
    distancia_total = 0
    for i in range(len(puntos_interpolados) - 1):
        lat1, lon1, _ = puntos_interpolados[i]
        lat2, lon2, _ = puntos_interpolados[i + 1]
        distancia_total += calcular_distancia_haversine(lat1, lon1, lat2, lon2)
    
    print(f"📏 Distancia total: {distancia_total:.2f} km")
    
    # Obtener o crear móvil OVV799
    with connection.cursor() as cursor:
        cursor.execute("SELECT id, patente, alias FROM moviles WHERE patente = 'OVV799' LIMIT 1")
        movil_data = cursor.fetchone()
        
        if not movil_data:
            print("🚙 Creando móvil OVV799...")
            cursor.execute("""
                INSERT INTO moviles (patente, alias, codigo, marca, modelo, activo, created_at, updated_at)
                VALUES ('OVV799', 'Taxi 799', 'OVV799', 'Chevrolet', 'Corsa', true, NOW(), NOW())
                RETURNING id, patente, alias
            """)
            movil_data = cursor.fetchone()
        
        movil_id, patente, alias = movil_data
        print(f"🚙 Usando móvil: {patente} - {alias}")
    
    # Usar empresa_id = 1
    empresa_id = 1
    print(f"🏢 Usando empresa ID: {empresa_id}")
    
    # Limpiar posiciones anteriores de este móvil
    print("🧹 Limpiando posiciones anteriores...")
    with connection.cursor() as cursor:
        cursor.execute("DELETE FROM posiciones WHERE movil_id = %s", [movil_id])
        posiciones_eliminadas = cursor.rowcount
        print(f"🗑️  Posiciones eliminadas: {posiciones_eliminadas}")
    
    # Generar posiciones - entre las 12hs y 13hs del día de ayer
    print("🕐 Iniciando recorrido...")
    
    # Calcular tiempo de inicio (ayer a las 12:00)
    ahora = datetime.now()
    ayer = ahora - timedelta(days=1)
    inicio_hora = ayer.replace(hour=12, minute=0, second=0, microsecond=0)
    
    tiempo_actual = inicio_hora
    posiciones_creadas = 0
    
    # Calcular tiempo total del viaje (aproximadamente 50-60 minutos para ~40 km)
    tiempo_total_viaje = len(puntos_interpolados) * 30  # 30 segundos promedio por punto
    
    print(f"⏰ Inicio del recorrido: {inicio_hora.strftime('%Y-%m-%d %H:%M:%S')}")
    
    for i, (lat, lon, descripcion) in enumerate(puntos_interpolados):
        # Determinar si estamos en autopista (puntos del medio)
        progreso = i / len(puntos_interpolados)
        es_autopista = 0.25 <= progreso <= 0.75  # Entre 25% y 75% del recorrido
        
        # Calcular velocidad realista
        if i > 0:
            lat_ant, lon_ant, _ = puntos_interpolados[i-1]
            distancia_anterior = calcular_distancia_haversine(lat_ant, lon_ant, lat, lon) * 1000
            velocidad = generar_velocidad_realista(distancia_anterior, es_autopista)
        else:
            velocidad = 0  # Inicio detenido
        
        # Calcular rumbo
        if i < len(puntos_interpolados) - 1:
            lat_sig, lon_sig, _ = puntos_interpolados[i + 1]
            rumbo = calcular_rumbo(lat, lon, lat_sig, lon_sig)
        else:
            rumbo = 0
        
        # Generar datos realistas
        altitud = random.randint(10, 50)
        satelites = random.randint(6, 12)
        hdop = round(random.uniform(1.0, 3.0), 2)
        accuracy = random.randint(3, 15)
        
        # Estado del vehículo
        ignicion = velocidad > 0 or random.random() > 0.1  # 90% de probabilidad de estar encendido
        bateria = random.randint(12000, 14000) if ignicion else random.randint(11000, 13000)
        
        # Tiempo entre posiciones (más realista)
        if velocidad > 0:
            tiempo_entre_posiciones = random.randint(15, 45)  # 15-45 segundos
        else:
            tiempo_entre_posiciones = random.randint(30, 120)  # 30 segundos a 2 minutos si está detenido
        
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
                f'msg_{i}_{int(tiempo_actual.timestamp())}', i, 'teltonika', 'FMB920',
                f'raw_data_{i}', True, False, False, tiempo_actual
            ])
        
        posiciones_creadas += 1
        
        # Mostrar progreso cada 20 posiciones
        if i % 20 == 0 or i == len(puntos_interpolados) - 1:
            print(f"📍 Posición {i+1}/{len(puntos_interpolados)}: {lat:.6f}, {lon:.6f} - {velocidad} km/h - {descripcion}")
    
    # Actualizar estado del móvil con la última posición
    if puntos_interpolados:
        ultima_lat, ultima_lon, ultima_desc = puntos_interpolados[-1]
        
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO moviles_status (movil_id, lat, lon, fec_gps, velocidad, rumbo, altitud, sats, ignicion, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                    ON CONFLICT (movil_id) DO UPDATE SET
                        lat = EXCLUDED.lat,
                        lon = EXCLUDED.lon,
                        fec_gps = EXCLUDED.fec_gps,
                        velocidad = EXCLUDED.velocidad,
                        rumbo = EXCLUDED.rumbo,
                        altitud = EXCLUDED.altitud,
                        sats = EXCLUDED.sats,
                        ignicion = EXCLUDED.ignicion,
                        updated_at = NOW()
                """, [movil_id, ultima_lat, ultima_lon, tiempo_actual, int(velocidad), rumbo, altitud, satelites, ignicion])
            
            print(f"✅ Estado del móvil actualizado: {ultima_desc}")
        except Exception as e:
            print(f"⚠️  No se pudo actualizar moviles_status: {e}")
            print(f"📍 Última posición: {ultima_desc} ({ultima_lat:.6f}, {ultima_lon:.6f})")
    
    print(f"\n🎉 Recorrido Fitz Roy -> Regimiento de Patricios completado!")
    print(f"📊 Estadísticas:")
    print(f"   - Posiciones creadas: {posiciones_creadas}")
    print(f"   - Distancia total: {distancia_total:.2f} km")
    print(f"   - Hora de inicio: {inicio_hora.strftime('%H:%M:%S')}")
    print(f"   - Hora de fin: {tiempo_actual.strftime('%H:%M:%S')}")
    print(f"   - Duración: {(tiempo_actual - inicio_hora).seconds // 60} minutos")
    
    return posiciones_creadas

if __name__ == '__main__':
    try:
        posiciones_creadas = generar_recorrido_fitzroy_regimiento()
        print(f"\n✅ Script completado exitosamente. {posiciones_creadas} posiciones creadas.")
    except Exception as e:
        print(f"❌ Error ejecutando el script: {e}")
        import traceback
        traceback.print_exc()
