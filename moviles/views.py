from django.db.models import Count
from django.shortcuts import render
from django.core.cache import cache
from rest_framework import permissions, viewsets
from rest_framework.response import Response

from .models import (Movil, MovilFoto, MovilGeocode, MovilNota,
                     MovilObservacion, MovilStatus)
from .serializers import (MovilGeocodeSerializer, MovilNotaSerializer,
                          MovilObservacionSerializer, MovilSerializer,
                          MovilStatusSerializer, MovilFotoSerializer)


class MovilViewSet(viewsets.ModelViewSet):
    """ViewSet optimizado para el modelo Movil"""

    queryset = Movil.objects.none()
    serializer_class = MovilSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        qs = (
            Movil.objects
            .all()
            .select_related('status', 'geocode', 'nota_general')
            .annotate(
                fotos_total=Count('fotos', distinct=True),
                observaciones_total=Count('observaciones', distinct=True)
            )
            .order_by('-updated_at', '-created_at')
        )

        if self.request.query_params.get('solo_activos') in {'1', 'true', 'True'}:
            qs = qs.filter(activo=True)
        return qs

    def list(self, request, *args, **kwargs):
        simple = request.query_params.get('simple')
        if simple in {'1', 'true', 'True'}:
            # Cache para lista simple de móviles
            cache_key = 'moviles_simple_list'
            data = cache.get(cache_key)
            if data is None:
                qs = (
                    Movil.objects
                    .filter(activo=True)
                    .only('id', 'alias', 'patente', 'codigo', 'gps_id')
                    .order_by('alias', 'patente', 'codigo')
                )
                data = [
                    {
                        'id': movil.id,
                        'alias': movil.alias,
                        'patente': movil.patente,
                        'codigo': movil.codigo,
                        'gps_id': movil.gps_id,
                        'display': (
                            movil.alias
                            or movil.patente
                            or movil.codigo
                            or movil.gps_id
                            or f"Movil #{movil.id}"
                        )
                    }
                    for movil in qs
                ]
                cache.set(cache_key, data, 60)  # Cache por 1 minuto
            return Response(data)
        return super().list(request, *args, **kwargs)


class MovilStatusViewSet(viewsets.ModelViewSet):
    """ViewSet para el modelo MovilStatus"""
    queryset = MovilStatus.objects.all()
    serializer_class = MovilStatusSerializer
    permission_classes = [permissions.AllowAny]


class MovilGeocodeViewSet(viewsets.ModelViewSet):
    """ViewSet para el modelo MovilGeocode"""
    queryset = MovilGeocode.objects.all()
    serializer_class = MovilGeocodeSerializer
    permission_classes = [permissions.AllowAny]


class MovilObservacionViewSet(viewsets.ModelViewSet):
    """ViewSet para el modelo MovilObservacion"""
    queryset = MovilObservacion.objects.all()
    serializer_class = MovilObservacionSerializer
    permission_classes = [permissions.AllowAny]


class MovilFotoViewSet(viewsets.ModelViewSet):
    """ViewSet para el modelo MovilFoto"""
    queryset = MovilFoto.objects.all()
    serializer_class = MovilFotoSerializer
    permission_classes = [permissions.AllowAny]


class MovilNotaViewSet(viewsets.ModelViewSet):
    """ViewSet para el modelo MovilNota"""
    queryset = MovilNota.objects.all()
    serializer_class = MovilNotaSerializer
    permission_classes = [permissions.AllowAny]


def moviles_list_view(request):
    """Vista para listado y gestión de móviles"""
    return render(request, 'moviles/index.html', {
        'default_section': 'moviles'
    })


def moviles_dashboard_view(request):
    """Vista de dashboard específico de móviles"""
    return render(request, 'moviles/index.html', {
        'default_section': 'dashboard'
    })


def moviles2_list_view(request):
    """Nueva vista para listado y gestión de móviles (versión limpia)"""
    return render(request, 'moviles2/index.html')


def dashboard2_view(request):
    """Nueva vista de dashboard separada"""
    return render(request, 'dashboard2/index.html')