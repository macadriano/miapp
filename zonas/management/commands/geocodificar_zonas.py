"""
Comando de gestión para geocodificar zonas existentes.
Ejecutar con: python manage.py geocodificar_zonas
"""
from django.core.management.base import BaseCommand
from django.db import models
from zonas.models import Zona
from zonas.services import reverse_geocode
from django.contrib.gis.geos import Point


class Command(BaseCommand):
    help = 'Geocodifica todas las zonas que no tienen dirección asignada'

    def add_arguments(self, parser):
        parser.add_argument(
            '--forzar',
            action='store_true',
            help='Forzar geocodificación de todas las zonas, incluso las que ya tienen dirección',
        )
        parser.add_argument(
            '--zona-id',
            type=int,
            help='Geocodificar solo una zona específica por su ID',
        )

    def handle(self, *args, **options):
        forzar = options['forzar']
        zona_id = options.get('zona_id')
        
        # Filtrar zonas según los argumentos
        if zona_id:
            zonas = Zona.objects.filter(id=zona_id)
            if not zonas.exists():
                self.stdout.write(self.style.ERROR(f'No se encontró una zona con ID {zona_id}'))
                return
        elif forzar:
            zonas = Zona.objects.all()
        else:
            # Solo zonas sin dirección
            zonas = Zona.objects.filter(
                models.Q(direccion__isnull=True) | 
                models.Q(direccion='') |
                models.Q(direccion_formateada__isnull=True) | 
                models.Q(direccion_formateada='')
            )
        
        total = zonas.count()
        if total == 0:
            self.stdout.write(self.style.SUCCESS('No hay zonas para geocodificar.'))
            return
        
        self.stdout.write(f'Geocodificando {total} zona(s)...')
        
        exitosas = 0
        fallidas = 0
        
        for zona in zonas:
            try:
                self.stdout.write(f'Procesando: {zona.nombre} (ID: {zona.id})...', ending=' ')
                
                # Extraer el punto según el tipo de zona (misma lógica que en el modelo)
                punto_geocodificar = None
                
                if zona.tipo == Zona.ZonaTipo.PUNTO:
                    if zona.geom and zona.geom.geom_type == 'Point':
                        punto_geocodificar = zona.geom
                elif zona.tipo == Zona.ZonaTipo.CIRCULO:
                    if zona.centro:
                        punto_geocodificar = zona.centro
                elif zona.tipo == Zona.ZonaTipo.POLIGONO:
                    if zona.geom and zona.geom.geom_type == 'Polygon':
                        try:
                            exterior_ring = zona.geom.exterior_ring
                            if exterior_ring and len(exterior_ring.coords) > 0:
                                first_coord = exterior_ring.coords[0]
                                lon, lat = first_coord[0], first_coord[1]
                                punto_geocodificar = Point(lon, lat, srid=4326)
                        except (AttributeError, IndexError, TypeError):
                            try:
                                centroide = zona.geom.centroid
                                punto_geocodificar = centroide
                            except Exception:
                                pass
                elif zona.tipo == Zona.ZonaTipo.POLILINEA:
                    if zona.geom and zona.geom.geom_type in ('LineString', 'MultiLineString'):
                        if zona.geom.geom_type == 'LineString':
                            coords = list(zona.geom.coords)
                        else:
                            coords = list(zona.geom[0].coords) if len(zona.geom) > 0 else []
                        
                        if coords and len(coords) > 0:
                            lon, lat = coords[0]
                            punto_geocodificar = Point(lon, lat, srid=4326)
                
                if not punto_geocodificar:
                    self.stdout.write(self.style.WARNING('Sin coordenadas'))
                    fallidas += 1
                    continue
                
                # Geocodificar
                direccion_data = reverse_geocode(
                    lat=float(punto_geocodificar.y),
                    lon=float(punto_geocodificar.x)
                )
                
                if direccion_data:
                    zona.direccion = direccion_data.get('direccion', '')
                    zona.direccion_formateada = direccion_data.get('direccion_formateada', '')
                    zona.save(update_fields=['direccion', 'direccion_formateada'])
                    self.stdout.write(self.style.SUCCESS('✓'))
                    exitosas += 1
                else:
                    self.stdout.write(self.style.WARNING('No se pudo geocodificar'))
                    fallidas += 1
                    
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error: {str(e)}'))
                fallidas += 1
        
        # Resumen
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(f'✓ Exitosas: {exitosas}'))
        if fallidas > 0:
            self.stdout.write(self.style.WARNING(f'✗ Fallidas: {fallidas}'))
        self.stdout.write(self.style.SUCCESS(f'Total procesadas: {total}'))

