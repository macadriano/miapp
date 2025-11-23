from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    MovilViewSet, MovilStatusViewSet, MovilGeocodeViewSet,
    MovilObservacionViewSet, MovilFotoViewSet, MovilNotaViewSet,
    moviles_list_view, moviles_dashboard_view
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
    # Frontend
    path('', moviles_list_view, name='moviles_list'),
    path('dashboard/', moviles_dashboard_view, name='moviles_dashboard'),

    # APIs
    path('api/', include(router.urls)),
]
