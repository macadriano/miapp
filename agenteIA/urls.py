from django.urls import path
from .views import sofia_frontend, procesar_consulta

urlpatterns = [
    path('', sofia_frontend, name='sofia_frontend'),
    path('api/procesar-consulta/', procesar_consulta, name='procesar_consulta'),
]

