from decimal import Decimal

from django.contrib.gis.db.models import fields as gis_fields
from django.contrib.postgres.operations import CreateExtension
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        CreateExtension("postgis"),
        migrations.CreateModel(
            name="Zona",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("nombre", models.CharField(max_length=100)),
                ("descripcion", models.TextField(blank=True)),
                (
                    "tipo",
                    models.CharField(
                        choices=[
                            ("punto", "Punto"),
                            ("circulo", "Círculo"),
                            ("poligono", "Polígono"),
                            ("polilinea", "Polilínea"),
                        ],
                        max_length=20,
                    ),
                ),
                ("geom", gis_fields.GeometryField(srid=4326)),
                ("centro", gis_fields.PointField(blank=True, null=True, srid=4326)),
                ("radio_metros", models.PositiveIntegerField(blank=True, null=True)),
                ("color", models.CharField(default="#FF0000", max_length=20)),
                ("opacidad", models.DecimalField(decimal_places=2, default=Decimal("0.50"), max_digits=3)),
                ("visible", models.BooleanField(default=True)),
                ("creado_en", models.DateTimeField(auto_now_add=True)),
                ("actualizado_en", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "Zona",
                "verbose_name_plural": "Zonas",
                "ordering": ("-actualizado_en", "nombre"),
            },
        ),
        migrations.AddIndex(
            model_name="zona",
            index=models.Index(fields=["tipo"], name="zonas_zona_tipo_f9f9a5_idx"),
        ),
    ]

