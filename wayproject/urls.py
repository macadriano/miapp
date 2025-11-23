from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from gps.views import (
    equipos_frontend, recorridos_frontend,
    comunicaciones_frontend, configuraciones_receptor_frontend,
    estadisticas_receptor_frontend, logs_receptor_frontend,
    mapa_frontend, reportes_frontend, controles_neo_frontend,
    receiver_stats, receiver_start, receiver_stop, receiver_stats,
    receiver_logs, receiver_log_content, test_api
)
from authentication.views import login_frontend

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('authentication.urls')),  # API de autenticación
    path('api/', include('gps.urls')),  # API de GPS
    path('api/', include('moviles.urls')),  # API de Móviles
    path('login/', login_frontend, name='login'),  # Página de login
    path('moviles/', include('moviles.urls')),  # URLs de móviles (API + Frontend)
    path('agenteIA/', include('agenteIA.urls')),  # URLs de Agente IA Sofia
    path('equipos/', equipos_frontend, name='equipos_frontend'),
    path('recorridos/', recorridos_frontend, name='recorridos_frontend'),
    path('zonas/', include('zonas.urls')),
    path('mapa/', mapa_frontend, name='mapa_frontend'),
    path('reportes/', reportes_frontend, name='reportes_frontend'),
    path('controles-neo/', controles_neo_frontend, name='controles_neo_frontend'),
    path('comunicaciones/', comunicaciones_frontend, name='comunicaciones_frontend'),
    path('comunicaciones/configuraciones/', configuraciones_receptor_frontend, name='configuraciones_receptor_frontend'),
    path('comunicaciones/estadisticas/', estadisticas_receptor_frontend, name='estadisticas_receptor_frontend'),
    path('comunicaciones/logs/', logs_receptor_frontend, name='logs_receptor_frontend'),
    # API endpoints para control de receptores
    path('api/receiver/stats/', receiver_stats, name='receiver_stats'),
    path('api/receiver/start/', receiver_start, name='receiver_start'),
    path('api/receiver/stop/', receiver_stop, name='receiver_stop'),
    path('api/receiver/status/', receiver_stats, name='receiver_status'),
    path('api/receiver/logs/', receiver_logs, name='receiver_logs'),
    path('api/receiver/log-content/', receiver_log_content, name='receiver_log_content'),
    path('api/test/', test_api, name='test_api'),
    path('', login_frontend, name='home'),  # Redirige raíz a login
]

# Servir archivos estáticos y media en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)