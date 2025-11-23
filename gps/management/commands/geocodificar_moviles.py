"""
Comando Django para geocodificar móviles
"""

from django.core.management.base import BaseCommand
from gps.services import geocoding_service
from moviles.models import Movil


class Command(BaseCommand):
    help = 'Geocodificar móviles con coordenadas usando OpenStreetMap'

    def add_arguments(self, parser):
        parser.add_argument(
            '--movil-id',
            type=int,
            help='ID específico del móvil a geocodificar',
        )
        parser.add_argument(
            '--patente',
            type=str,
            help='Patente específica del móvil a geocodificar',
        )
        parser.add_argument(
            '--todos',
            action='store_true',
            help='Geocodificar todos los móviles con coordenadas',
        )
        parser.add_argument(
            '--forzar',
            action='store_true',
            help='Forzar geocodificación incluso si ya existe',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('=== GEOCODIFICACION DE MOVILES ===')
        )

        if options['movil_id']:
            # Geocodificar móvil específico por ID
            try:
                movil = Movil.objects.get(id=options['movil_id'])
                self.stdout.write(f'Geocodificando móvil: {movil.patente}')
                
                if geocoding_service.actualizar_geocodificacion_movil(movil.id):
                    self.stdout.write(
                        self.style.SUCCESS(f'Móvil {movil.patente} geocodificado exitosamente')
                    )
                else:
                    self.stdout.write(
                        self.style.ERROR(f'Error geocodificando móvil {movil.patente}')
                    )
                    
            except Movil.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'No se encontró móvil con ID {options["movil_id"]}')
                )

        elif options['patente']:
            # Geocodificar móvil específico por patente
            try:
                movil = Movil.objects.get(patente=options['patente'])
                self.stdout.write(f'Geocodificando móvil: {movil.patente}')
                
                if geocoding_service.actualizar_geocodificacion_movil(movil.id):
                    self.stdout.write(
                        self.style.SUCCESS(f'Móvil {movil.patente} geocodificado exitosamente')
                    )
                else:
                    self.stdout.write(
                        self.style.ERROR(f'Error geocodificando móvil {movil.patente}')
                    )
                    
            except Movil.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'No se encontró móvil con patente {options["patente"]}')
                )

        elif options['todos']:
            # Geocodificar todos los móviles
            self.stdout.write('Geocodificando todos los móviles con coordenadas...')
            
            moviles_geocodificados = geocoding_service.geocodificar_todos_los_moviles()
            
            self.stdout.write(
                self.style.SUCCESS(f'Geocodificación completada: {moviles_geocodificados} móviles')
            )

        else:
            # Mostrar ayuda
            self.stdout.write(
                self.style.WARNING('Debe especificar una opción:')
            )
            self.stdout.write('  --movil-id ID        Geocodificar móvil específico por ID')
            self.stdout.write('  --patente PATENTE    Geocodificar móvil específico por patente')
            self.stdout.write('  --todos              Geocodificar todos los móviles con coordenadas')
            
            # Mostrar móviles disponibles
            moviles_con_coordenadas = Movil.objects.filter(
                status__ultimo_lat__isnull=False,
                status__ultimo_lon__isnull=False
            ).exclude(
                status__ultimo_lat='',
                status__ultimo_lon=''
            )
            
            if moviles_con_coordenadas.exists():
                self.stdout.write('\nMóviles disponibles con coordenadas:')
                for movil in moviles_con_coordenadas:
                    self.stdout.write(f'  ID {movil.id}: {movil.patente} ({movil.alias})')
            else:
                self.stdout.write('\nNo hay móviles con coordenadas para geocodificar.')
