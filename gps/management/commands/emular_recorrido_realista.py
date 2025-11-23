from django.core.management.base import BaseCommand
from django.utils import timezone
from gps.models import Posicion
from moviles.models import Movil, MovilStatus, MovilGeocode
from datetime import datetime, timedelta
import random
import math


class Command(BaseCommand):
    help = 'Emula un recorrido realista entre Fitz Roy 6185, Isidro Casanova y Italia 1157, Burzaco'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🚗 Iniciando emulación de recorrido realista...'))
        
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
        distancia_total = self.calcular_distancia_haversine(
            origen['lat'], origen['lon'],
            destino['lat'], destino['lon']
        )
        
        self.stdout.write(f"📍 Origen: {origen['direccion']}")
        self.stdout.write(f"📍 Destino: {destino['direccion']}")
        self.stdout.write(f"📏 Distancia total: {distancia_total/1000:.2f} km")
        
        # Configuración del viaje
        tiempo_total_minutos = 60  # 1 hora
        intervalo_posiciones = 100  # metros entre posiciones
        num_posiciones = int(distancia_total / intervalo_posiciones)
        
        self.stdout.write(f"⏱️  Tiempo estimado: {tiempo_total_minutos} minutos")
        self.stdout.write(f"📍 Posiciones a generar: {num_posiciones}")
        
        # Obtener un móvil existente
        movil = Movil.objects.first()
        if not movil:
            self.stdout.write(self.style.WARNING('❌ No hay móviles en la base de datos. Creando uno de prueba...'))
            movil = Movil.objects.create(
                patente='TEST001',
                alias='Móvil de Prueba',
                codigo='T001',
                marca='Toyota',
                modelo='Hilux',
                activo=True
            )
        
        self.stdout.write(f"🚙 Usando móvil: {movil.patente} - {movil.alias}")
        
        # Generar coordenadas interpoladas
        coordenadas = self.interpolar_coordenadas(
            origen['lat'], origen['lon'],
            destino['lat'], destino['lon'],
            num_posiciones
        )
        
        # Generar velocidades realistas
        velocidades = self.generar_velocidad_realista(distancia_total, tiempo_total_minutos)
        
        # Ajustar el número de velocidades al número de posiciones
        if len(velocidades) < len(coordenadas):
            velocidades.extend([velocidades[-1]] * (len(coordenadas) - len(velocidades)))
        elif len(velocidades) > len(coordenadas):
            velocidades = velocidades[:len(coordenadas)]
        
        # Tiempo de inicio
        tiempo_inicio = timezone.now() - timedelta(hours=2)  # Hace 2 horas
        tiempo_entre_posiciones = timedelta(minutes=tiempo_total_minutos / len(coordenadas))
        
        self.stdout.write(f"🕐 Iniciando recorrido a las: {tiempo_inicio.strftime('%H:%M:%S')}")
        
        # Limpiar posiciones anteriores del móvil
        Posicion.objects.filter(movil=movil).delete()
        
        posiciones_creadas = 0
        
        # Crear posiciones
        for i, (lat, lon) in enumerate(coordenadas):
            tiempo_posicion = tiempo_inicio + (tiempo_entre_posiciones * i)
            velocidad = velocidades[i]
            
            # Calcular rumbo (dirección)
            if i < len(coordenadas) - 1:
                lat_sig, lon_sig = coordenadas[i + 1]
                rumbo = self.calcular_rumbo(lat, lon, lat_sig, lon_sig)
            else:
                rumbo = self.calcular_rumbo(coordenadas[i-1][0], coordenadas[i-1][1], lat, lon)
            
            # Determinar si el motor está encendido (basado en velocidad)
            ignicion = velocidad > 0
            
            # Generar datos de satélites realistas
            satelites = random.randint(6, 12)
            hdop = round(random.uniform(1.0, 3.0), 2)
            accuracy_m = random.randint(5, 20)
            
            # Crear posición
            posicion = Posicion.objects.create(
                empresa_id=1,  # Usar empresa_id=1 directamente
                device_id=12345,  # Device ID de prueba
                movil=movil,
                fec_gps=tiempo_posicion,
                fec_report=tiempo_posicion,
                evento='POS',
                velocidad=int(velocidad),
                rumbo=int(rumbo),
                lat=round(lat, 7),
                lon=round(lon, 7),
                altitud=random.randint(10, 50),
                sats=satelites,
                hdop=hdop,
                accuracy_m=accuracy_m,
                ign_on=ignicion,
                batt_mv=random.randint(12000, 14000),
                ext_pwr_mv=random.randint(13000, 15000),
                inputs_mask='00000000',
                outputs_mask='00000000',
                msg_uid=f'MSG_{i:06d}',
                seq=i,
                provider='teltonika',
                protocol='tcp',
                is_valid=True,
                is_late=False,
                is_duplicate=False
            )
            
            posiciones_creadas += 1
            
            if i % 20 == 0:  # Mostrar progreso cada 20 posiciones
                self.stdout.write(f"📍 Posición {i+1}/{len(coordenadas)}: {lat:.6f}, {lon:.6f} - {velocidad:.1f} km/h")
        
        # Actualizar MovilStatus con la última posición
        ultima_posicion = Posicion.objects.filter(movil=movil).order_by('-fec_gps').first()
        
        if ultima_posicion:
            MovilStatus.objects.update_or_create(
                movil=movil,
                defaults={
                    'ultimo_lat': ultima_posicion.lat,
                    'ultimo_lon': ultima_posicion.lon,
                    'ultima_velocidad_kmh': ultima_posicion.velocidad,
                    'bateria_pct': random.randint(70, 95),
                    'satelites': ultima_posicion.sats,
                    'estado_conexion': 'conectado',
                    'ultima_actualizacion': ultima_posicion.fec_gps,
                    'ignicion': ultima_posicion.ign_on,
                    'odometro_km': random.uniform(10000.0, 150000.0),
                    'horas_motor': random.uniform(500.0, 5000.0),
                    'temperatura_motor': random.uniform(70.0, 95.0),
                    'nivel_combustible_pct': random.randint(20, 100),
                    'direccion_manual': destino['direccion']
                }
            )
            
            self.stdout.write(self.style.SUCCESS(f"✅ MovilStatus actualizado para {movil.alias}"))
        
        # Actualizar MovilGeocode con la última posición
        MovilGeocode.objects.update_or_create(
            movil=movil,
            defaults={
                'lat': ultima_posicion.lat,
                'lon': ultima_posicion.lon,
                'direccion_formateada': destino['direccion'],
                'pais': 'Argentina',
                'provincia': 'Buenos Aires',
                'ciudad': 'Burzaco',
                'codigo_postal': '1852',
                'fecha_actualizacion': timezone.now()
            }
        )
        
        self.stdout.write(self.style.SUCCESS(f"✅ MovilGeocode actualizado para {movil.alias}"))
        
        self.stdout.write(self.style.SUCCESS(f"\n🎉 Recorrido completado exitosamente!"))
        self.stdout.write(f"📊 Estadísticas:")
        self.stdout.write(f"   - Posiciones creadas: {posiciones_creadas}")
        self.stdout.write(f"   - Distancia total: {distancia_total/1000:.2f} km")
        self.stdout.write(f"   - Tiempo total: {tiempo_total_minutos} minutos")
        self.stdout.write(f"   - Velocidad promedio: {distancia_total/1000/(tiempo_total_minutos/60):.1f} km/h")
        self.stdout.write(f"   - Última posición: {destino['direccion']}")
        
        return posiciones_creadas

    def calcular_distancia_haversine(self, lat1, lon1, lat2, lon2):
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

    def interpolar_coordenadas(self, lat1, lon1, lat2, lon2, num_puntos):
        """Interpola coordenadas entre dos puntos"""
        coordenadas = []
        
        for i in range(num_puntos + 1):
            factor = i / num_puntos
            
            lat = lat1 + (lat2 - lat1) * factor
            lon = lon1 + (lon2 - lon1) * factor
            
            coordenadas.append((lat, lon))
        
        return coordenadas

    def generar_velocidad_realista(self, distancia_total_m, tiempo_total_min):
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

    def calcular_rumbo(self, lat1, lon1, lat2, lon2):
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
