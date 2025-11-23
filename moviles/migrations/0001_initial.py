# Revised initial migration that matches the consolidated schema already presente en BD

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.CreateModel(
                    name='Movil',
                    fields=[
                        ('id', models.BigAutoField(primary_key=True, serialize=False)),
                        ('codigo', models.CharField(blank=True, max_length=32, null=True, unique=True)),
                        ('alias', models.CharField(blank=True, max_length=100, null=True)),
                        ('patente', models.CharField(blank=True, max_length=20, null=True, unique=True)),
                        ('vin', models.CharField(blank=True, max_length=17, null=True)),
                        ('marca', models.TextField(blank=True, null=True)),
                        ('modelo', models.TextField(blank=True, null=True)),
                        ('anio', models.SmallIntegerField(blank=True, null=True)),
                        ('color', models.TextField(blank=True, null=True)),
                        ('tipo_vehiculo', models.CharField(blank=True, max_length=20, null=True)),
                        ('gps_id', models.CharField(blank=True, max_length=50, null=True, unique=True)),
                        ('activo', models.BooleanField(default=True)),
                        ('created_at', models.DateTimeField(auto_now_add=True)),
                        ('updated_at', models.DateTimeField(auto_now=True)),
                    ],
                    options={
                        'db_table': 'moviles',
                        'verbose_name': 'Móvil',
                        'verbose_name_plural': 'Móviles',
                    },
                ),
                migrations.CreateModel(
                    name='MovilGeocode',
                    fields=[
                        ('movil', models.OneToOneField(on_delete=models.CASCADE, primary_key=True, related_name='geocode', serialize=False, to='moviles.movil')),
                        ('direccion_formateada', models.TextField(blank=True, null=True)),
                        ('calle', models.CharField(blank=True, max_length=200, null=True)),
                        ('numero', models.CharField(blank=True, max_length=20, null=True)),
                        ('piso', models.CharField(blank=True, max_length=20, null=True)),
                        ('depto', models.CharField(blank=True, max_length=20, null=True)),
                        ('barrio', models.CharField(blank=True, max_length=100, null=True)),
                        ('localidad', models.CharField(blank=True, max_length=100, null=True)),
                        ('municipio', models.CharField(blank=True, max_length=100, null=True)),
                        ('provincia', models.CharField(blank=True, max_length=100, null=True)),
                        ('codigo_postal', models.CharField(blank=True, max_length=20, null=True)),
                        ('pais', models.CharField(default='Argentina', max_length=100)),
                        ('fuente_geocodificacion', models.CharField(blank=True, max_length=50, null=True)),
                        ('confianza_geocodificacion', models.DecimalField(blank=True, decimal_places=2, max_digits=3, null=True)),
                        ('geohash', models.CharField(blank=True, max_length=20, null=True)),
                        ('fecha_geocodificacion', models.DateTimeField(blank=True, null=True)),
                        ('fecha_actualizacion', models.DateTimeField(auto_now=True)),
                    ],
                    options={
                        'db_table': 'moviles_geocode',
                        'verbose_name': 'Geocodificación de Móvil',
                        'verbose_name_plural': 'Geocodificaciones de Móviles',
                        'indexes': [
                            models.Index(fields=['provincia', 'localidad'], name='moviles_geo_provin_7758aa_idx'),
                            models.Index(fields=['fecha_geocodificacion'], name='moviles_geo_fecha_g_27dbab_idx'),
                        ],
                    },
                ),
                migrations.CreateModel(
                    name='MovilStatus',
                    fields=[
                        ('movil', models.OneToOneField(on_delete=models.CASCADE, primary_key=True, related_name='status', serialize=False, to='moviles.movil')),
                        ('ultimo_lat', models.DecimalField(blank=True, decimal_places=6, max_digits=10, null=True)),
                        ('ultimo_lon', models.DecimalField(blank=True, decimal_places=6, max_digits=10, null=True)),
                        ('ultima_altitud', models.DecimalField(blank=True, decimal_places=2, max_digits=8, null=True)),
                        ('ultima_velocidad_kmh', models.DecimalField(blank=True, decimal_places=2, max_digits=6, null=True)),
                        ('ultimo_rumbo', models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True)),
                        ('satelites', models.SmallIntegerField(blank=True, null=True)),
                        ('hdop', models.DecimalField(blank=True, decimal_places=2, max_digits=4, null=True)),
                        ('calidad_senal', models.SmallIntegerField(blank=True, null=True)),
                        ('ignicion', models.BooleanField(default=False)),
                        ('bateria_pct', models.SmallIntegerField(blank=True, null=True)),
                        ('odometro_km', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                        ('estado_conexion', models.CharField(choices=[('conectado', 'Conectado'), ('desconectado', 'Desconectado'), ('error', 'Error')], default='desconectado', max_length=20)),
                        ('fecha_gps', models.DateTimeField(blank=True, null=True)),
                        ('fecha_recepcion', models.DateTimeField(blank=True, null=True)),
                        ('ultima_actualizacion', models.DateTimeField(auto_now=True)),
                        ('id_ultima_posicion', models.BigIntegerField(blank=True, null=True)),
                        ('raw_data', models.TextField(blank=True, null=True)),
                        ('raw_json', models.JSONField(blank=True, null=True)),
                    ],
                    options={
                        'db_table': 'moviles_status',
                        'verbose_name': 'Estado de Móvil',
                        'verbose_name_plural': 'Estados de Móviles',
                        'indexes': [
                            models.Index(fields=['estado_conexion'], name='moviles_sta_estado__383ade_idx'),
                            models.Index(fields=['fecha_gps'], name='moviles_sta_fecha_gp_b0e393_idx'),
                            models.Index(fields=['ultima_actualizacion'], name='moviles_sta_ultima_a_6bb179_idx'),
                        ],
                    },
                ),
                migrations.CreateModel(
                    name='MovilNota',
                    fields=[
                        ('movil', models.OneToOneField(on_delete=models.CASCADE, primary_key=True, related_name='nota_general', serialize=False, to='moviles.movil')),
                        ('contenido', models.TextField(blank=True, help_text='Notas generales sobre el móvil')),
                        ('fecha_creacion', models.DateTimeField(auto_now_add=True)),
                        ('fecha_actualizacion', models.DateTimeField(auto_now=True)),
                        ('usuario_actualizacion', models.ForeignKey(null=True, on_delete=models.SET_NULL, to=settings.AUTH_USER_MODEL)),
                    ],
                    options={
                        'db_table': 'moviles_notas',
                        'verbose_name': 'Nota de Móvil',
                        'verbose_name_plural': 'Notas de Móviles',
                    },
                ),
                migrations.CreateModel(
                    name='MovilObservacion',
                    fields=[
                        ('id', models.BigAutoField(primary_key=True, serialize=False)),
                        ('titulo', models.CharField(max_length=200)),
                        ('contenido', models.TextField()),
                        ('categoria', models.CharField(choices=[('general', 'General'), ('mantenimiento', 'Mantenimiento'), ('incidente', 'Incidente'), ('documentacion', 'Documentación'), ('reparacion', 'Reparación'), ('inspeccion', 'Inspección')], default='general', max_length=50)),
                        ('prioridad', models.CharField(choices=[('baja', 'Baja'), ('media', 'Media'), ('alta', 'Alta'), ('urgente', 'Urgente')], default='media', max_length=20)),
                        ('estado', models.CharField(choices=[('abierta', 'Abierta'), ('en_proceso', 'En Proceso'), ('cerrada', 'Cerrada'), ('cancelada', 'Cancelada')], default='abierta', max_length=20)),
                        ('fecha_creacion', models.DateTimeField(auto_now_add=True)),
                        ('fecha_actualizacion', models.DateTimeField(auto_now=True)),
                        ('fecha_vencimiento', models.DateTimeField(blank=True, null=True)),
                        ('movil', models.ForeignKey(on_delete=models.CASCADE, related_name='observaciones', to='moviles.movil')),
                        ('usuario_asignado', models.ForeignKey(blank=True, null=True, on_delete=models.SET_NULL, related_name='observaciones_asignadas', to=settings.AUTH_USER_MODEL)),
                        ('usuario_creacion', models.ForeignKey(null=True, on_delete=models.SET_NULL, related_name='observaciones_creadas', to=settings.AUTH_USER_MODEL)),
                    ],
                    options={
                        'db_table': 'moviles_observaciones',
                        'ordering': ['-fecha_creacion'],
                        'verbose_name': 'Observación de Móvil',
                        'verbose_name_plural': 'Observaciones de Móviles',
                        'indexes': [
                            models.Index(fields=['movil', 'fecha_creacion'], name='moviles_obs_movil_id__0b3bc6_idx'),
                            models.Index(fields=['categoria'], name='moviles_obs_categoria_592cc7_idx'),
                            models.Index(fields=['estado'], name='moviles_obs_estado_c746e9_idx'),
                            models.Index(fields=['prioridad'], name='moviles_obs_priorida_b13c51_idx'),
                        ],
                    },
                ),
                migrations.CreateModel(
                    name='MovilFoto',
                    fields=[
                        ('id', models.BigAutoField(primary_key=True, serialize=False)),
                        ('imagen', models.ImageField(help_text='Imagen del móvil', upload_to='moviles/fotos/%Y/%m/')),
                        ('titulo', models.CharField(blank=True, max_length=200)),
                        ('descripcion', models.TextField(blank=True)),
                        ('categoria', models.CharField(choices=[('exterior', 'Exterior'), ('interior', 'Interior'), ('documentos', 'Documentos'), ('danos', 'Daños'), ('mantenimiento', 'Mantenimiento'), ('accesorios', 'Accesorios'), ('general', 'General')], default='general', max_length=50)),
                        ('tamaño_archivo', models.IntegerField(blank=True, help_text='Tamaño en bytes', null=True)),
                        ('dimensiones', models.CharField(blank=True, help_text='Ancho x Alto en píxeles', max_length=20)),
                        ('latitud', models.DecimalField(blank=True, decimal_places=6, max_digits=10, null=True)),
                        ('longitud', models.DecimalField(blank=True, decimal_places=6, max_digits=10, null=True)),
                        ('orden', models.IntegerField(default=0, help_text='Orden de visualización')),
                        ('es_principal', models.BooleanField(default=False, help_text='Foto principal del móvil')),
                        ('visible', models.BooleanField(default=True)),
                        ('fecha_captura', models.DateTimeField(auto_now_add=True)),
                        ('fecha_actualizacion', models.DateTimeField(auto_now=True)),
                        ('movil', models.ForeignKey(on_delete=models.CASCADE, related_name='fotos', to='moviles.movil')),
                        ('observacion', models.ForeignKey(blank=True, null=True, on_delete=models.SET_NULL, related_name='fotos', to='moviles.movilobservacion')),
                        ('usuario_captura', models.ForeignKey(blank=True, null=True, on_delete=models.SET_NULL, related_name='fotos_capturadas', to=settings.AUTH_USER_MODEL)),
                    ],
                    options={
                        'db_table': 'moviles_fotos',
                        'ordering': ['orden', '-fecha_captura'],
                        'verbose_name': 'Foto de Móvil',
                        'verbose_name_plural': 'Fotos de Móviles',
                        'indexes': [
                            models.Index(fields=['movil', 'orden'], name='moviles_fot_movil_id__4bdd7d_idx'),
                            models.Index(fields=['categoria'], name='moviles_fot_categoria_8198f2_idx'),
                            models.Index(fields=['es_principal'], name='moviles_fot_es_princi_112a67_idx'),
                            models.Index(fields=['fecha_captura'], name='moviles_fot_fecha_cap_cb72bd_idx'),
                        ],
                        'constraints': [
                            models.UniqueConstraint(condition=models.Q(('es_principal', True)), fields=('movil',), name='unique_foto_principal_por_movil'),
                        ],
                    },
                ),
            ],
        ),
    ]
