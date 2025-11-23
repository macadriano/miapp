from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import GeocodeAutocompleteView, ZonaViewSet, ZonasTemplateView

router = DefaultRouter()
router.register(r"zonas", ZonaViewSet, basename="zona")

urlpatterns = [
    path("", ZonasTemplateView.as_view(), name="zonas_frontend"),
    path("api/geocode/autocomplete/", GeocodeAutocompleteView.as_view(), name="zonas_geocode_autocomplete"),
    path("api/", include(router.urls)),
]

