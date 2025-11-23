# Generated manually to add direccion fields to Zona model

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('zonas', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='zona',
            name='direccion',
            field=models.CharField(blank=True, help_text='Dirección geocodificada de la zona', max_length=500, null=True),
        ),
        migrations.AddField(
            model_name='zona',
            name='direccion_formateada',
            field=models.TextField(blank=True, help_text='Dirección completa formateada', null=True),
        ),
    ]

