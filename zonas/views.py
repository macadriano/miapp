import json

from django.contrib.auth.decorators import login_required
from django.contrib.gis.geos import Point
from django.core.cache import cache
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from rest_framework import filters, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from moviles.models import Movil, MovilStatus
from .models import Zona
from .serializers import ZonaSerializer
from .services import geocode_search


class ZonaViewSet(viewsets.ModelViewSet):
    serializer_class = ZonaSerializer
    queryset = Zona.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["nombre", "descripcion", "tipo"]
    ordering_fields = ["nombre", "tipo", "actualizado_en", "creado_en"]
    ordering = ["-actualizado_en"]

    @action(detail=False, methods=["post"], url_path="crear-desde-movil")
    def crear_desde_movil(self, request):
        movil_id = request.data.get("movil_id")
        tipo = (request.data.get("tipo") or "punto").lower()
        if tipo not in ("punto", "circulo"):
            return Response({"error": "El tipo debe ser 'punto' o 'circulo'."}, status=status.HTTP_400_BAD_REQUEST)

        if not movil_id:
            return Response({"error": "movil_id es obligatorio."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            movil = Movil.objects.get(id=movil_id)
        except Movil.DoesNotExist:
            return Response({"error": "El móvil indicado no existe."}, status=status.HTTP_404_NOT_FOUND)

        status_obj = MovilStatus.objects.filter(movil=movil).first()
        if not status_obj or not status_obj.ultimo_lat or not status_obj.ultimo_lon:
            return Response(
                {"error": "El móvil no tiene una posición actual disponible."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            lat = float(status_obj.ultimo_lat)
            lon = float(status_obj.ultimo_lon)
        except (TypeError, ValueError):
            return Response(
                {"error": "La posición almacenada del móvil es inválida."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        centro_point = Point(lon, lat, srid=4326)
        centro_geojson = json.loads(centro_point.geojson)

        color = request.data.get("color") or "#FF0000"
        opacidad = request.data.get("opacidad", 0.5)
        visible = request.data.get("visible", True)
        nombre = request.data.get("nombre") or f"Zona {movil.alias or movil.patente or movil.codigo or movil_id}"
        descripcion = request.data.get("descripcion") or f"Generada desde {movil.alias or movil.patente or movil.codigo or 'móvil'}"

        geom_geojson = centro_geojson
        radio_metros = None

        if tipo == "circulo":
            radio_metros = request.data.get("radio_metros")
            try:
                radio_metros = int(radio_metros)
            except (TypeError, ValueError):
                return Response({"error": "El radio debe ser un número entero."}, status=status.HTTP_400_BAD_REQUEST)
            if radio_metros <= 0:
                return Response({"error": "El radio debe ser mayor a 0."}, status=status.HTTP_400_BAD_REQUEST)

            buffered = centro_point.transform(3857, clone=True).buffer(radio_metros).transform(4326, clone=True)
            geom_geojson = json.loads(buffered.geojson)

        payload = {
            "nombre": nombre,
            "descripcion": descripcion,
            "tipo": tipo,
            "color": color,
            "opacidad": opacidad,
            "visible": visible,
            "geom_geojson_input": geom_geojson,
        }

        if tipo == "circulo":
            payload["centro_geojson_input"] = centro_geojson
            payload["radio_metros"] = radio_metros

        serializer = self.get_serializer(data=payload)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=status.HTTP_201_CREATED)


@method_decorator(login_required, name="dispatch")
class ZonasTemplateView(TemplateView):
    template_name = "zonas/index.html"


class GeocodeAutocompleteView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        query = request.query_params.get("q", "")
        limit = request.query_params.get("limit") or 5
        try:
            limit = max(1, min(int(limit), 10))
        except (TypeError, ValueError):
            limit = 5

        suggestions = geocode_search(query, limit=limit)
        return Response({"results": suggestions})

