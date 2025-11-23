# Generated manually

from django.db import migrations

def create_default_tipo_equipo(apps, schema_editor):
    """Crear tipo de equipo GPS por defecto si no existe"""
    TipoEquipoGPS = apps.get_model('gps', 'TipoEquipoGPS')
    
    # Verificar si ya existe
    if not TipoEquipoGPS.objects.filter(id=1).exists():
        TipoEquipoGPS.objects.create(
            id=1,
            codigo='TQ',
            nombre='Queclink TQ',
            fabricante='Queclink',
            protocolo='TCP',
            puerto_default=5003,
            formato_datos={'type': 'binary'},
            activo=True
        )

def reverse_migration(apps, schema_editor):
    """Eliminar tipo de equipo GPS por defecto"""
    TipoEquipoGPS = apps.get_model('gps', 'TipoEquipoGPS')
    TipoEquipoGPS.objects.filter(id=1).delete()

class Migration(migrations.Migration):

    dependencies = [
        ('gps', '0011_add_transporte_to_configuracion_receptor'),
    ]

    operations = [
        migrations.RunPython(create_default_tipo_equipo, reverse_migration),
    ]
