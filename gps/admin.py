from django.contrib import admin
from .models import Equipo


# MovilAdmin se movió a moviles/admin.py


@admin.register(Equipo)
class EquipoAdmin(admin.ModelAdmin):
    list_display = ['imei', 'marca', 'modelo', 'estado', 'fecha_instalacion', 'created_at']
    list_filter = ['estado', 'marca', 'created_at']
    search_fields = ['imei', 'numero_serie', 'marca', 'modelo']
    ordering = ['-created_at']


# Register your models here.
