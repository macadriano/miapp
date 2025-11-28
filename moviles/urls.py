from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    MovilViewSet, MovilStatusViewSet, MovilGeocodeViewSet,
    MovilObservacionViewSet, MovilFotoViewSet, MovilNotaViewSet,
    moviles_list_view, moviles_dashboard_view,
    moviles2_list_view, dashboard2_view
)

# Router para las APIs
router = DefaultRouter()
router.register(r'moviles', MovilViewSet)
router.register(r'moviles-status', MovilStatusViewSet)
router.register(r'moviles-geocode', MovilGeocodeViewSet)
router.register(r'moviles-observaciones', MovilObservacionViewSet)
router.register(r'moviles-fotos', MovilFotoViewSet)
router.register(r'moviles-notas', MovilNotaViewSet)

urlpatterns = [
    # Frontend (versión antigua - mantener por compatibilidad)
    path('', moviles_list_view, name='moviles_list'),
    path('dashboard/', moviles_dashboard_view, name='moviles_dashboard'),
    
    # Frontend (nueva versión limpia)
    path('v2/', moviles2_list_view, name='moviles2_list'),
    path('dashboard2/', dashboard2_view, name='dashboard2'),

    # APIs
    path('api/', include(router.urls)),
]
