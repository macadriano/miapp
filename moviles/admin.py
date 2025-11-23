from django.contrib import admin
from .models import Movil, MovilStatus, MovilGeocode, MovilObservacion, MovilFoto, MovilNota


@admin.register(Movil)
class MovilAdmin(admin.ModelAdmin):
    list_display = ['patente', 'alias', 'gps_id', 'marca', 'modelo', 'activo']
    list_filter = ['activo', 'marca', 'tipo_vehiculo']
    search_fields = ['patente', 'alias', 'gps_id', 'vin']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(MovilStatus)
class MovilStatusAdmin(admin.ModelAdmin):
    list_display = ['movil', 'estado_conexion', 'ultima_velocidad_kmh', 'fecha_gps']
    list_filter = ['estado_conexion', 'ignicion']
    search_fields = ['movil__patente', 'movil__alias']


@admin.register(MovilGeocode)
class MovilGeocodeAdmin(admin.ModelAdmin):
    list_display = ['movil', 'localidad', 'provincia', 'fecha_geocodificacion']
    list_filter = ['provincia', 'localidad']
    search_fields = ['movil__patente', 'movil__alias', 'direccion_formateada']


@admin.register(MovilObservacion)
class MovilObservacionAdmin(admin.ModelAdmin):
    list_display = ['movil', 'titulo', 'categoria', 'prioridad', 'estado']
    list_filter = ['categoria', 'prioridad', 'estado']
    search_fields = ['movil__patente', 'movil__alias', 'titulo']


@admin.register(MovilFoto)
class MovilFotoAdmin(admin.ModelAdmin):
    list_display = ['movil', 'titulo', 'categoria', 'es_principal']
    list_filter = ['categoria', 'es_principal']
    search_fields = ['movil__patente', 'movil__alias', 'titulo']


@admin.register(MovilNota)
class MovilNotaAdmin(admin.ModelAdmin):
    list_display = ['movil', 'fecha_actualizacion']
    search_fields = ['movil__patente', 'movil__alias']
