from moviles.models import Movil, MovilStatus, MovilGeocode
from django.utils import timezone
import random


datos = [
    ('CAMION3', -34.588, -58.430, 'Av. Santa Fe 3500, Palermo, CABA'),
    ('CAMION4', -34.618, -58.445, 'Av. Rivadavia 5200, Caballito, CABA'),
    ('CAMION5', -34.633, -58.456, 'Av. Avellaneda 3500, Flores, CABA'),
    ('CAMION6', -34.648, -58.378, 'Av. Montes de Oca 900, Barracas, CABA'),
    ('CAMION7', -34.662, -58.364, 'Mitre 100, Avellaneda, Buenos Aires'),
    ('CAMION8', -34.699, -58.392, 'Av. Hipólito Yrigoyen 4500, Lanús, Buenos Aires'),
    ('CAMION9', -34.760, -58.401, 'Av. Hipólito Yrigoyen 8700, Lomas de Zamora, Buenos Aires'),
    ('CAMION10', -34.720, -58.252, 'Av. Calchaquí 1100, Quilmes, Buenos Aires'),
    ('CAMION11', -34.426, -58.576, 'Av. Cazón 900, Tigre, Buenos Aires'),
    ('CAMION12', -34.472, -58.512, 'Av. Centenario 200, San Isidro, Buenos Aires'),
    ('CAMION13', -34.653, -58.619, 'Av. Rivadavia 18000, Morón, Buenos Aires'),
]

creados = []
for alias, lat, lon, direccion in datos:
    movil, created = Movil.objects.get_or_create(
        alias=alias,
        defaults={'patente': alias, 'codigo': alias, 'gps_id': f'IMEI_{alias}', 'activo': True}
    )

    if not created:
        # Asegurar que campos clave estén presentes
        if not movil.patente:
            movil.patente = alias
        if not movil.codigo:
            movil.codigo = alias
        if not movil.gps_id:
            movil.gps_id = f'IMEI_{alias}'
        movil.activo = True
        movil.save(update_fields=['patente', 'codigo', 'gps_id', 'activo'])

    MovilStatus.objects.update_or_create(
        movil=movil,
        defaults={
            'ultimo_lat': lat,
            'ultimo_lon': lon,
            'ultima_velocidad_kmh': random.uniform(10, 60),
            'estado_conexion': 'conectado',
            'fecha_gps': timezone.now(),
            'fecha_recepcion': timezone.now()
        }
    )

    MovilGeocode.objects.update_or_create(
        movil=movil,
        defaults={
            'direccion_formateada': direccion,
            'localidad': 'Buenos Aires',
            'provincia': 'Buenos Aires',
            'pais': 'Argentina',
            'fecha_geocodificacion': timezone.now()
        }
    )

    creados.append(alias)

print('Creados:', creados)
