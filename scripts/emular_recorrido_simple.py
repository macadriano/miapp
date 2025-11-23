#!/usr/bin/env python
"""
Script simple para emular un recorrido realista usando SQL directo
"""

import os
import sys
import django
from datetime import datetime, timedelta
import random
import math

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
    
    return R * c * 1000  # Retorna en metros

def interpolar_coordenadas(lat1, lon1, lat2, lon2, num_puntos):
    """Interpola coordenadas entre dos puntos"""
    coordenadas = []
    
    for i in range(num_puntos + 1):
        factor = i / num_puntos
        
        lat = lat1 + (lat2 - lat1) * factor
        lon = lon1 + (lon2 - lon1) * factor
        
        coordenadas.append((lat, lon))
    
    return coordenadas

def generar_velocidad_realista(distancia_total_m, tiempo_total_min):
    """Genera velocidades realistas para un viaje"""
    # Velocidad promedio esperada
    velocidad_promedio = (distancia_total_m / 1000) / (tiempo_total_min / 60)  # km/h
    
    # Simular variaciones realistas
    velocidades = []
    
    # Inicio del viaje (aceleración)
    for i in range(5):
        velocidad = min(velocidad_promedio * 0.3 + (i * 5), 30)
        velocidades.append(velocidad)
    
    # Viaje principal (velocidades variables)
    for i in range(30):
        # Velocidad base con variaciones
        base_vel = velocidad_promedio
        variacion = random.uniform(-10, 15)  # Variación de velocidad
        
        # Simular semáforos y tráfico (velocidades bajas ocasionales)
        if random.random() < 0.1:  # 10% de probabilidad de estar detenido
            velocidad = random.uniform(0, 5)
        elif random.random() < 0.2:  # 20% de probabilidad de velocidad baja
            velocidad = random.uniform(10, 25)
        else:
            velocidad = max(0, base_vel + variacion)
            velocidad = min(velocidad, 80)  # Límite máximo
        
        velocidades.append(velocidad)
    
    # Final del viaje (desaceleración)
    for i in range(5):
        velocidad = max(velocidad_promedio * 0.5 - (i * 8), 0)
        velocidades.append(velocidad)
    
    return velocidades

def calcular_rumbo(lat1, lon1, lat2, lon2):
    """Calcula el rumbo entre dos puntos"""
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    dlon_rad = math.radians(lon2 - lon1)
    
    y = math.sin(dlon_rad) * math.cos(lat2_rad)
    x = math.cos(lat1_rad) * math.sin(lat2_rad) - math.sin(lat1_rad) * math.cos(lat2_rad) * math.cos(dlon_rad)
    
    rumbo_rad = math.atan2(y, x)
    rumbo_grados = math.degrees(rumbo_rad)
    
    # Normalizar a 0-360 grados
    rumbo_grados = (rumbo_grados + 360) % 360
    
    return rumbo_grados

def generar_recorrido_simple():
    """Genera un recorrido realista usando SQL directo"""
    
    print("🚗 Iniciando emulación de recorrido realista...")
    
    # Coordenadas de origen y destino
    origen = {
        'lat': -34.7012,
        'lon': -58.5834,
        'direccion': 'Fitz Roy 6185, Isidro Casanova, Buenos Aires'
    }
    
    destino = {
        'lat': -34.8244,
        'lon': -58.3832,
        'direccion': 'Italia 1157, Burzaco, Buenos Aires'
    }
    
    # Calcular distancia total
    distancia_total = calcular_distancia_haversine(
        origen['lat'], origen['lon'],
        destino['lat'], destino['lon']
    )
    
    print(f"📍 Origen: {origen['direccion']}")
    print(f"📍 Destino: {destino['direccion']}")
    print(f"📏 Distancia total: {distancia_total/1000:.2f} km")
    
    # Configuración del viaje
    tiempo_total_minutos = 60  # 1 hora
    intervalo_posiciones = 100  # metros entre posiciones
    num_posiciones = int(distancia_total / intervalo_posiciones)
    
    print(f"⏱️  Tiempo estimado: {tiempo_total_minutos} minutos")
    print(f"📍 Posiciones a generar: {num_posiciones}")
    
    # Obtener un móvil existente
    with connection.cursor() as cursor:
        cursor.execute("SELECT id, patente, alias FROM moviles LIMIT 1")
        result = cursor.fetchone()
        
        if not result:
            print("❌ No hay móviles en la base de datos. Creando uno de prueba...")
            cursor.execute("""
                INSERT INTO moviles (patente, alias, codigo, marca, modelo, activo)
                VALUES ('TEST001', 'Móvil de Prueba', 'T001', 'Toyota', 'Hilux', true)
            """)
            cursor.execute("SELECT id, patente, alias FROM moviles WHERE patente = 'TEST001'")
            result = cursor.fetchone()
        
        movil_id, patente, alias = result
        print(f"🚙 Usando móvil: {patente} - {alias}")
        
        # Limpiar posiciones anteriores del móvil
        cursor.execute("DELETE FROM posiciones WHERE movil_id = %s", [movil_id])
        print("🧹 Posiciones anteriores eliminadas")
        
        # Generar coordenadas interpoladas
        coordenadas = interpolar_coordenadas(
            origen['lat'], origen['lon'],
            destino['lat'], destino['lon'],
            num_posiciones
        )
        
        # Generar velocidades realistas
        velocidades = generar_velocidad_realista(distancia_total, tiempo_total_minutos)
        
        # Ajustar el número de velocidades al número de posiciones
        if len(velocidades) < len(coordenadas):
            velocidades.extend([velocidades[-1]] * (len(coordenadas) - len(velocidades)))
        elif len(velocidades) > len(coordenadas):
            velocidades = velocidades[:len(coordenadas)]
        
        # Tiempo de inicio
        tiempo_inicio = datetime.now() - timedelta(hours=2)  # Hace 2 horas
        tiempo_entre_posiciones = timedelta(minutes=tiempo_total_minutos / len(coordenadas))
        
        print(f"🕐 Iniciando recorrido a las: {tiempo_inicio.strftime('%H:%M:%S')}")
        
        posiciones_creadas = 0
        
        # Crear posiciones usando SQL directo
        for i, (lat, lon) in enumerate(coordenadas):
            tiempo_posicion = tiempo_inicio + (tiempo_entre_posiciones * i)
            velocidad = velocidades[i]
            
            # Calcular rumbo (dirección)
            if i < len(coordenadas) - 1:
                lat_sig, lon_sig = coordenadas[i + 1]
                rumbo = calcular_rumbo(lat, lon, lat_sig, lon_sig)
            else:
                rumbo = calcular_rumbo(coordenadas[i-1][0], coordenadas[i-1][1], lat, lon)
            
            # Determinar si el motor está encendido (basado en velocidad)
            ignicion = velocidad > 0
            
            # Generar datos de satélites realistas
            satelites = random.randint(6, 12)
            hdop = round(random.uniform(1.0, 3.0), 2)
            accuracy_m = random.randint(5, 20)
            
            # Insertar posición usando SQL directo
            cursor.execute("""
                INSERT INTO posiciones (
                    empresa_id, device_id, movil_id, fec_gps, fec_report, evento,
                    velocidad, rumbo, lat, lon, altitud, sats, hdop, accuracy_m,
                    ign_on, batt_mv, ext_pwr_mv, inputs_mask, outputs_mask,
                    msg_uid, seq, provider, protocol, is_valid, is_late, is_duplicate,
                    created_at
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
            """, [
                1,  # empresa_id
                12345,  # device_id
                movil_id,  # movil_id
                tiempo_posicion,  # fec_gps
                tiempo_posicion,  # fec_report
                'POS',  # evento
                int(velocidad),  # velocidad
                int(rumbo),  # rumbo
                round(lat, 7),  # lat
                round(lon, 7),  # lon
                random.randint(10, 50),  # altitud
                satelites,  # sats
                hdop,  # hdop
                accuracy_m,  # accuracy_m
                ignicion,  # ign_on
                random.randint(12000, 14000),  # batt_mv
                random.randint(13000, 15000),  # ext_pwr_mv
                '00000000',  # inputs_mask
                '00000000',  # outputs_mask
                f'MSG_{i:06d}',  # msg_uid
                i,  # seq
                'teltonika',  # provider
                'tcp',  # protocol
                True,  # is_valid
                False,  # is_late
                False,  # is_duplicate
                datetime.now()  # created_at
            ])
            
            posiciones_creadas += 1
            
            if i % 20 == 0:  # Mostrar progreso cada 20 posiciones
                print(f"📍 Posición {i+1}/{len(coordenadas)}: {lat:.6f}, {lon:.6f} - {velocidad:.1f} km/h")
        
        # Actualizar MovilStatus con la última posición
        ultima_posicion = coordenadas[-1]
        ultima_velocidad = velocidades[-1]
        
        cursor.execute("""
            INSERT INTO moviles_status (
                movil_id, ultimo_lat, ultimo_lon, ultima_velocidad_kmh,
                bateria_pct, satelites, estado_conexion, ultima_actualizacion,
                ignicion, odometro_km, horas_motor, temperatura_motor,
                nivel_combustible_pct, direccion_manual
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            ON CONFLICT (movil_id) DO UPDATE SET
                ultimo_lat = EXCLUDED.ultimo_lat,
                ultimo_lon = EXCLUDED.ultimo_lon,
                ultima_velocidad_kmh = EXCLUDED.ultima_velocidad_kmh,
                bateria_pct = EXCLUDED.bateria_pct,
                satelites = EXCLUDED.satelites,
                estado_conexion = EXCLUDED.estado_conexion,
                ultima_actualizacion = EXCLUDED.ultima_actualizacion,
                ignicion = EXCLUDED.ignicion,
                odometro_km = EXCLUDED.odometro_km,
                horas_motor = EXCLUDED.horas_motor,
                temperatura_motor = EXCLUDED.temperatura_motor,
                nivel_combustible_pct = EXCLUDED.nivel_combustible_pct,
                direccion_manual = EXCLUDED.direccion_manual
        """, [
            movil_id,
            ultima_posicion[0],
            ultima_posicion[1],
            int(ultima_velocidad),
            random.randint(70, 95),
            random.randint(8, 12),
            'conectado',
            datetime.now(),
            ultima_velocidad > 0,
            random.uniform(10000.0, 150000.0),
            random.uniform(500.0, 5000.0),
            random.uniform(70.0, 95.0),
            random.randint(20, 100),
            destino['direccion']
        ])
        
        print("✅ MovilStatus actualizado")
        
        # Actualizar MovilGeocode con la última posición
        cursor.execute("""
            INSERT INTO moviles_geocode (
                movil_id, lat, lon, direccion_formateada, pais, provincia,
                ciudad, codigo_postal, fecha_actualizacion
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            ON CONFLICT (movil_id) DO UPDATE SET
                lat = EXCLUDED.lat,
                lon = EXCLUDED.lon,
                direccion_formateada = EXCLUDED.direccion_formateada,
                pais = EXCLUDED.pais,
                provincia = EXCLUDED.provincia,
                ciudad = EXCLUDED.ciudad,
                codigo_postal = EXCLUDED.codigo_postal,
                fecha_actualizacion = EXCLUDED.fecha_actualizacion
        """, [
            movil_id,
            ultima_posicion[0],
            ultima_posicion[1],
            destino['direccion'],
            'Argentina',
            'Buenos Aires',
            'Burzaco',
            '1852',
            datetime.now()
        ])
        
        print("✅ MovilGeocode actualizado")
        
        print(f"\n🎉 Recorrido completado exitosamente!")
        print(f"📊 Estadísticas:")
        print(f"   - Posiciones creadas: {posiciones_creadas}")
        print(f"   - Distancia total: {distancia_total/1000:.2f} km")
        print(f"   - Tiempo total: {tiempo_total_minutos} minutos")
        print(f"   - Velocidad promedio: {distancia_total/1000/(tiempo_total_minutos/60):.1f} km/h")
        print(f"   - Última posición: {destino['direccion']}")
        
        return posiciones_creadas

if __name__ == '__main__':
    try:
        posiciones_creadas = generar_recorrido_simple()
        print(f"\n✅ Script ejecutado exitosamente. {posiciones_creadas} posiciones creadas.")
    except Exception as e:
        print(f"❌ Error ejecutando el script: {str(e)}")
        import traceback
        traceback.print_exc()
