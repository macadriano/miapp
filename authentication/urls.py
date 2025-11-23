from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    login_view, logout_view, perfil_actual, permisos_usuario, cambiar_password,
    UsuarioViewSet, RolViewSet, PerfilViewSet, PermisoEntidadViewSet,
    login_frontend
)

router = DefaultRouter()
router.register(r'usuarios', UsuarioViewSet, basename='usuario')
router.register(r'roles', RolViewSet, basename='rol')
router.register(r'perfiles', PerfilViewSet, basename='perfil')
router.register(r'permisos-entidad', PermisoEntidadViewSet, basename='permiso-entidad')

urlpatterns = [
    # API endpoints
    path('login/', login_view, name='api_login'),
    path('logout/', logout_view, name='api_logout'),
    path('me/', perfil_actual, name='perfil_actual'),
    path('permisos/', permisos_usuario, name='permisos_usuario'),
    path('cambiar-password/', cambiar_password, name='cambiar_password'),
    
    # Rutas del router
    path('', include(router.urls)),
]

