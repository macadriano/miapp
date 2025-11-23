# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gps', '0010_create_equipos_gps_table'),
    ]

    operations = [
        migrations.AddField(
            model_name='configuracionreceptor',
            name='transporte',
            field=models.CharField(
                choices=[('TCP', 'TCP'), ('UDP', 'UDP'), ('HTTP', 'HTTP')],
                default='TCP',
                max_length=10
            ),
        ),
    ]
