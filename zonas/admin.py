from django.contrib import admin

from .models import Zona


@admin.register(Zona)
class ZonaAdmin(admin.ModelAdmin):
    list_display = ("nombre", "tipo", "visible", "color", "actualizado_en")
    list_filter = ("tipo", "visible")
    search_fields = ("nombre", "descripcion")
    readonly_fields = ("creado_en", "actualizado_en")

