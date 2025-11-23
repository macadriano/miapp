from __future__ import annotations

from decimal import Decimal

from django.contrib.gis.db import models as gis_models
from django.contrib.gis.geos import GEOSGeometry, Point
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _


class Zona(gis_models.Model):
    class ZonaTipo(models.TextChoices):
        PUNTO = "punto", _("Punto")
        CIRCULO = "circulo", _("Círculo")
        POLIGONO = "poligono", _("Polígono")
        POLILINEA = "polilinea", _("Polilínea")

    nombre = gis_models.CharField(max_length=100)
    descripcion = gis_models.TextField(blank=True)
    tipo = gis_models.CharField(max_length=20, choices=ZonaTipo.choices)
    geom = gis_models.GeometryField(srid=4326)
    centro = gis_models.PointField(srid=4326, null=True, blank=True)
    radio_metros = gis_models.PositiveIntegerField(null=True, blank=True)
    color = gis_models.CharField(max_length=20, default="#FF0000")
    opacidad = gis_models.DecimalField(
        max_digits=3, decimal_places=2, default=Decimal("0.50")
    )
    visible = gis_models.BooleanField(default=True)
    # Campos de geocodificación
    direccion = models.CharField(max_length=500, blank=True, null=True, help_text="Dirección geocodificada de la zona")
    direccion_formateada = models.TextField(blank=True, null=True, help_text="Dirección completa formateada")
    creado_en = gis_models.DateTimeField(auto_now_add=True)
    actualizado_en = gis_models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Zona"
        verbose_name_plural = "Zonas"
        ordering = ("-actualizado_en", "nombre")
        indexes = [
            models.Index(fields=("tipo",)),
        ]

    def __str__(self) -> str:
        return self.nombre

    def clean(self) -> None:
        super().clean()

        if self.tipo == self.ZonaTipo.CIRCULO:
            if not self.centro:
                raise ValidationError({"centro": _("El centro es obligatorio para círculos.")})
            if not self.radio_metros:
                raise ValidationError({"radio_metros": _("El radio es obligatorio para círculos.")})
        else:
            if self.centro or self.radio_metros:
                raise ValidationError(
                    _("Solo las zonas de tipo círculo pueden tener centro y radio definidos.")
                )

        if self.opacidad and not (Decimal("0") <= self.opacidad <= Decimal("1")):
            raise ValidationError({"opacidad": _("La opacidad debe estar entre 0 y 1.")})

    def save(self, *args, **kwargs):
        self._ensure_geom_for_circle()
        # Geocodificar la dirección antes de guardar
        self._geocodificar_direccion()
        super().save(*args, **kwargs)
    
    def _geocodificar_direccion(self) -> None:
        """
        Geocodifica la dirección de la zona usando reverse geocoding.
        Extrae el punto según el tipo de zona y obtiene la dirección.
        """
        from .services import reverse_geocode
        
        punto_geocodificar = None
        
        # Extraer el punto según el tipo de zona
        if self.tipo == self.ZonaTipo.PUNTO:
            # Para punto, usar el punto directamente
            if self.geom and self.geom.geom_type == 'Point':
                punto_geocodificar = self.geom
        elif self.tipo == self.ZonaTipo.CIRCULO:
            # Para círculo, usar el centro
            if self.centro:
                punto_geocodificar = self.centro
        elif self.tipo == self.ZonaTipo.POLIGONO:
            # Para polígono, usar el primer punto del exterior ring
            if self.geom and self.geom.geom_type == 'Polygon':
                try:
                    # Obtener el exterior ring del polígono
                    exterior_ring = self.geom.exterior_ring
                    if exterior_ring and len(exterior_ring.coords) > 0:
                        # El primer punto del exterior ring
                        first_coord = exterior_ring.coords[0]
                        lon, lat = first_coord[0], first_coord[1]
                        punto_geocodificar = Point(lon, lat, srid=4326)
                except (AttributeError, IndexError, TypeError):
                    # Fallback: usar el centroide del polígono
                    try:
                        centroide = self.geom.centroid
                        punto_geocodificar = centroide
                    except Exception:
                        pass
        elif self.tipo == self.ZonaTipo.POLILINEA:
            # Para polilínea, usar el primer punto
            if self.geom and self.geom.geom_type in ('LineString', 'MultiLineString'):
                if self.geom.geom_type == 'LineString':
                    coords = list(self.geom.coords)
                else:
                    # MultiLineString: tomar el primer punto de la primera línea
                    coords = list(self.geom[0].coords) if len(self.geom) > 0 else []
                
                if coords and len(coords) > 0:
                    lon, lat = coords[0]
                    punto_geocodificar = Point(lon, lat, srid=4326)
        
        # Si tenemos un punto, geocodificar
        if punto_geocodificar:
            try:
                direccion_data = reverse_geocode(
                    lat=float(punto_geocodificar.y),
                    lon=float(punto_geocodificar.x)
                )
                if direccion_data:
                    self.direccion = direccion_data.get('direccion', '')
                    self.direccion_formateada = direccion_data.get('direccion_formateada', '')
                else:
                    # Si no se pudo geocodificar, limpiar campos
                    self.direccion = ''
                    self.direccion_formateada = ''
            except Exception as e:
                # Si hay error en geocodificación, no fallar el guardado
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Error geocodificando zona {self.nombre}: {e}")
                self.direccion = ''
                self.direccion_formateada = ''
        else:
            # Si no hay punto para geocodificar, limpiar campos
            self.direccion = ''
            self.direccion_formateada = ''

    def _ensure_geom_for_circle(self) -> None:
        if self.tipo != self.ZonaTipo.CIRCULO or not self.centro:
            return

        if not isinstance(self.centro, Point):
            self.centro = GEOSGeometry(self.centro)

        centro = self.centro.clone()
        centro.srid = 4326

        projected = centro.transform(3857, clone=True)
        buffered = projected.buffer(self.radio_metros)
        buffered.srid = 3857
        buffered = buffered.transform(4326, clone=True)

        self.geom = buffered

