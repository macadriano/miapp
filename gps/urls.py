from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    EquipoViewSet, PosicionViewSet, CatMovilViewSet, TipoEquipoGPSViewSet, 
    ConfiguracionReceptorViewSet, EstadisticasRecepcionViewSet, RecorridosViewSet,
    recorridos_frontend, receiver_stats, receiver_start, receiver_stop, diagnostico_performance
)

router = DefaultRouter()
router.register(r'equipos', EquipoViewSet)
router.register(r'posiciones', PosicionViewSet)
router.register(r'cat-moviles', CatMovilViewSet)
router.register(r'tipos-equipos-gps', TipoEquipoGPSViewSet)
router.register(r'configuraciones-receptores', ConfiguracionReceptorViewSet)
router.register(r'estadisticas-recepcion', EstadisticasRecepcionViewSet)
router.register(r'recorridos', RecorridosViewSet, basename='recorrido')

urlpatterns = [
    path('', include(router.urls)),
    path('recorridos/', recorridos_frontend, name='recorridos_frontend'),
    # API endpoints para control del receptor
    path('receiver/stats/', receiver_stats, name='receiver_stats'),
    path('receiver/start/', receiver_start, name='receiver_start'),
    path('receiver/stop/', receiver_stop, name='receiver_stop'),
    path('receiver/status/', receiver_stats, name='receiver_status'),
    # Diagnóstico de performance
    path('diagnostico/', diagnostico_performance, name='diagnostico_performance'),
]