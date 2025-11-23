import json

from django.contrib.gis.geos import GEOSGeometry
from rest_framework import serializers

from .models import Zona


class ZonaSerializer(serializers.ModelSerializer):
    geom_geojson = serializers.SerializerMethodField(read_only=True)
    centro_geojson = serializers.SerializerMethodField(read_only=True)
    geom_geojson_input = serializers.JSONField(write_only=True, required=False)
    centro_geojson_input = serializers.JSONField(write_only=True, required=False)

    class Meta:
        model = Zona
        fields = [
            "id",
            "nombre",
            "descripcion",
            "tipo",
            "geom",
            "geom_geojson",
            "geom_geojson_input",
            "centro",
            "centro_geojson",
            "centro_geojson_input",
            "radio_metros",
            "color",
            "opacidad",
            "visible",
            "direccion",
            "direccion_formateada",
            "creado_en",
            "actualizado_en",
        ]
        read_only_fields = ("geom", "centro", "direccion", "direccion_formateada", "creado_en", "actualizado_en")

    def _geojson_to_geometry(self, data):
        if not data:
            return None
        if isinstance(data, (dict, list)):
            data = json.dumps(data)
        geometry = GEOSGeometry(data)
        geometry.srid = 4326
        return geometry

    def validate(self, attrs):
        tipo = attrs.get("tipo") or getattr(self.instance, "tipo", None)
        radio = attrs.get("radio_metros", getattr(self.instance, "radio_metros", None))
        centro_input = attrs.get("centro_geojson_input")

        if tipo == Zona.ZonaTipo.CIRCULO:
            if not centro_input and not (attrs.get("centro") or getattr(self.instance, "centro", None)):
                raise serializers.ValidationError("El centro es obligatorio para zonas circulares.")
            if not radio:
                raise serializers.ValidationError("El radio (en metros) es obligatorio para zonas circulares.")
        else:
            attrs.pop("centro_geojson_input", None)
            attrs.pop("radio_metros", None)

        if "opacidad" in attrs:
            opacidad = attrs["opacidad"]
            if not (0 <= float(opacidad) <= 1):
                raise serializers.ValidationError("La opacidad debe estar entre 0 y 1.")

        return attrs

    def create(self, validated_data):
        geom_geojson = validated_data.pop("geom_geojson_input", None)
        centro_geojson = validated_data.pop("centro_geojson_input", None)

        if geom_geojson:
            validated_data["geom"] = self._geojson_to_geometry(geom_geojson)

        if centro_geojson:
            validated_data["centro"] = self._geojson_to_geometry(centro_geojson)

        return super().create(validated_data)

    def update(self, instance, validated_data):
        geom_geojson = validated_data.pop("geom_geojson_input", None)
        centro_geojson = validated_data.pop("centro_geojson_input", None)

        if geom_geojson:
            validated_data["geom"] = self._geojson_to_geometry(geom_geojson)

        if centro_geojson:
            validated_data["centro"] = self._geojson_to_geometry(centro_geojson)

        return super().update(instance, validated_data)

    def get_geom_geojson(self, obj):
        return json.loads(obj.geom.geojson) if obj.geom else None

    def get_centro_geojson(self, obj):
        return json.loads(obj.centro.geojson) if obj.centro else None

