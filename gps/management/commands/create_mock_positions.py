"""
Comando Django para crear posiciones simuladas de móviles
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from moviles.models import Movil, MovilStatus, MovilGeocode
import random


class Command(BaseCommand):
    help = 'Crear posiciones simuladas para los móviles existentes'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Forzar actualización aunque ya existan posiciones',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🚗 Iniciando creación de posiciones simuladas...')
        )

        # Coordenadas de las direcciones específicas
        posiciones_mock = [
            {
                'direccion': 'Fitz Roy 6185, Isidro Casanova, Buenos Aires',
                'latitud': -34.7012,
                'longitud': -58.5834,
                'velocidad': 0.0,  # Estacionado
                'ignicion': False,
                'bateria': 85,
                'satelites': 8,
                'estado': 'conectado'
            },
            {
                'direccion': 'Italia 1157, Burzaco, Buenos Aires',
                'latitud': -34.8244,
                'longitud': -58.3832,
                'velocidad': 0.0,  # Estacionado
                'ignicion': False,
                'bateria': 92,
                'satelites': 10,
                'estado': 'conectado'
            }
        ]

        # Obtener todos los móviles existentes
        moviles = Movil.objects.all()
        
        if not moviles.exists():
            self.stdout.write(
                self.style.ERROR('❌ No hay móviles en la base de datos')
            )
            return

        self.stdout.write(
            self.style.WARNING(f'📱 Encontrados {moviles.count()} móviles')
        )

        moviles_actualizados = 0

        for i, movil in enumerate(moviles):
            # Usar posición mock correspondiente o generar una aleatoria
            if i < len(posiciones_mock):
                posicion = posiciones_mock[i]
                self.stdout.write(
                    self.style.SUCCESS(f'📍 Asignando posición específica: {posicion["direccion"]}')
                )
            else:
                # Generar posición aleatoria en Buenos Aires
                posicion = self._generar_posicion_aleatoria()
                self.stdout.write(
                    self.style.WARNING(f'🎲 Generando posición aleatoria para móvil extra')
                )

            try:
                # Verificar si ya existe MovilStatus
                status, created = MovilStatus.objects.get_or_create(
                    movil=movil,
                    defaults=self._crear_datos_status(movil, posicion)
                )

                if not created and not options['force']:
                    self.stdout.write(
                        self.style.WARNING(
                            f'⚠️  Móvil {movil.patente or movil.alias or "ID " + str(movil.id)} ya tiene posición. Usa --force para actualizar'
                        )
                    )
                    continue

                # Actualizar datos del status
                self._actualizar_datos_status(status, posicion)
                status.save()

                self.stdout.write(
                    self.style.SUCCESS(
                        f'✅ Móvil {movil.patente or movil.alias or "ID " + str(movil.id)}: '
                        f'Lat: {posicion["latitud"]}, Lon: {posicion["longitud"]}, '
                        f'Batería: {posicion["bateria"]}%, Satélites: {posicion["satelites"]}'
                    )
                )

                moviles_actualizados += 1

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f'❌ Error actualizando móvil {movil.patente or movil.alias or "ID " + str(movil.id)}: {e}'
                    )
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'🎉 Proceso completado: {moviles_actualizados} móviles actualizados'
            )
        )

        # Mostrar información sobre geocodificación
        self.stdout.write(
            self.style.WARNING(
                '💡 Las direcciones se geocodificarán automáticamente mediante signals'
            )
        )

    def _crear_datos_status(self, movil, posicion):
        """Crear datos iniciales para MovilStatus"""
        return {
            'ultimo_lat': posicion['latitud'],
            'ultimo_lon': posicion['longitud'],
            'ultima_altitud': random.randint(10, 50),  # Altitud aleatoria
            'ultima_velocidad_kmh': posicion['velocidad'],
            'ultimo_rumbo': random.randint(0, 359),  # Rumbo aleatorio
            'satelites': posicion['satelites'],
            'hdop': round(random.uniform(1.0, 3.0), 2),  # HDOP aleatorio
            'calidad_senal': random.randint(70, 95),  # Calidad de señal
            'ignicion': posicion['ignicion'],
            'bateria_pct': posicion['bateria'],
            'odometro_km': round(random.uniform(1000, 50000), 2),  # Odómetro aleatorio
            'estado_conexion': posicion['estado'],
            'fecha_gps': timezone.now(),
            'fecha_recepcion': timezone.now(),
            'ultima_actualizacion': timezone.now(),
            'raw_data': f'Mock data for {movil.patente or movil.alias}',
            'raw_json': {
                'mock': True,
                'timestamp': timezone.now().isoformat(),
                'source': 'management_command'
            }
        }

    def _actualizar_datos_status(self, status, posicion):
        """Actualizar datos existentes de MovilStatus"""
        status.ultimo_lat = posicion['latitud']
        status.ultimo_lon = posicion['longitud']
        status.ultima_velocidad_kmh = posicion['velocidad']
        status.ignicion = posicion['ignicion']
        status.bateria_pct = posicion['bateria']
        status.satelites = posicion['satelites']
        status.estado_conexion = posicion['estado']
        status.fecha_gps = timezone.now()
        status.fecha_recepcion = timezone.now()
        status.ultima_actualizacion = timezone.now()

    def _generar_posicion_aleatoria(self):
        """Generar posición aleatoria en Buenos Aires"""
        return {
            'direccion': 'Posición aleatoria en Buenos Aires',
            'latitud': round(random.uniform(-34.9, -34.5), 4),
            'longitud': round(random.uniform(-58.8, -58.2), 4),
            'velocidad': round(random.uniform(0, 60), 2),
            'ignicion': random.choice([True, False]),
            'bateria': random.randint(20, 100),
            'satelites': random.randint(5, 12),
            'estado': random.choice(['conectado', 'desconectado'])
        }
