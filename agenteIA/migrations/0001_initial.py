# Generated migration for agenteIA models

from django.conf import settings
import django.contrib.gis.db.models.fields
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='VectorConsulta',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('texto_original', models.TextField(help_text='Texto de ejemplo de la consulta del usuario')),
                ('categoria', models.CharField(choices=[('saludo', 'Saludo'), ('pasado', 'Consultas Pasadas'), ('actual', 'Estado Actual'), ('futuro', 'Consultas Futuras'), ('comando', 'Comandos')], max_length=20)),
                ('tipo_consulta', models.CharField(choices=[('POSICION', 'Posición del Móvil'), ('RECORRIDO', 'Recorrido Histórico'), ('ESTADO', 'Estado del Móvil'), ('COMANDO_WHATSAPP', 'Comando: Enviar por WhatsApp'), ('LLEGADA', 'Estimación de Llegada'), ('SALUDO', 'Saludo')], max_length=50)),
                ('vector_embedding', models.JSONField(default=list, help_text='Vector embedding de la consulta')),
                ('accion_asociada', models.TextField(help_text='Descripción de qué acción realizar cuando la consulta coincida')),
                ('threshold', models.FloatField(default=0.885, help_text='Umbral mínimo de similitud para considerar la consulta (0-1)')),
                ('variables', models.JSONField(blank=True, default=dict, help_text="Variables a extraer del texto (ej: {'movil': r'\\b[A-Z0-9]{3,10}\\b'})")),
                ('respuesta_template', models.TextField(blank=True, help_text='Plantilla de respuesta para esta consulta')),
                ('activo', models.BooleanField(default=True, help_text='Si está activo para usar en las consultas')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Vector de Consulta',
                'verbose_name_plural': 'Vectores de Consulta',
                'ordering': ['categoria', 'tipo_consulta'],
            },
        ),
        migrations.CreateModel(
            name='ZonaInteres',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=100)),
                ('descripcion', models.TextField(blank=True)),
                ('latitud', models.FloatField()),
                ('longitud', models.FloatField()),
                ('radio_metros', models.IntegerField(default=100, help_text='Radio de la zona en metros')),
                ('activo', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('usuario', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='zonas_interes', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Zona de Interés',
                'verbose_name_plural': 'Zonas de Interés',
                'ordering': ['nombre'],
            },
        ),
        migrations.CreateModel(
            name='ConversacionSofia',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('mensaje_usuario', models.TextField()),
                ('respuesta_sofia', models.TextField()),
                ('similitud', models.FloatField(blank=True, help_text='Nivel de similitud con el vector de consulta', null=True)),
                ('datos_consulta', models.JSONField(blank=True, default=dict, help_text="Datos extraídos de la consulta (móvil, fecha, etc)")),
                ('procesado', models.BooleanField(default=True, help_text='Si la consulta fue procesada exitosamente')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('usuario', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='conversaciones_sofia', to=settings.AUTH_USER_MODEL)),
                ('vector_usado', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='conversaciones', to='agenteIA.vectorconsulta')),
            ],
            options={
                'verbose_name': 'Conversación con Sofia',
                'verbose_name_plural': 'Conversaciones con Sofia',
                'ordering': ['-created_at'],
            },
        ),
    ]

