from django.contrib import admin
from .models import VectorConsulta, ConversacionSofia, ZonaInteres


@admin.register(VectorConsulta)
class VectorConsultaAdmin(admin.ModelAdmin):
    list_display = ['categoria', 'tipo_consulta', 'texto_original_short', 'threshold', 'activo', 'created_at']
    list_filter = ['categoria', 'tipo_consulta', 'activo']
    search_fields = ['texto_original', 'accion_asociada']
    list_editable = ['activo']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Información de la Consulta', {
            'fields': ('texto_original', 'categoria', 'tipo_consulta', 'activo')
        }),
        ('Vectorización', {
            'fields': ('vector_embedding', 'threshold')
        }),
        ('Acción y Respuesta', {
            'fields': ('accion_asociada', 'respuesta_template', 'variables')
        }),
        ('Metadatos', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def texto_original_short(self, obj):
        return obj.texto_original[:80] + '...' if len(obj.texto_original) > 80 else obj.texto_original
    texto_original_short.short_description = 'Texto Original'


@admin.register(ConversacionSofia)
class ConversacionSofiaAdmin(admin.ModelAdmin):
    list_display = ['usuario', 'mensaje_short', 'similitud', 'procesado', 'created_at']
    list_filter = ['procesado', 'created_at', 'vector_usado']
    search_fields = ['mensaje_usuario', 'respuesta_sofia', 'usuario__username']
    readonly_fields = ['created_at']
    
    def mensaje_short(self, obj):
        return obj.mensaje_usuario[:50] + '...' if len(obj.mensaje_usuario) > 50 else obj.mensaje_usuario
    mensaje_short.short_description = 'Mensaje'


@admin.register(ZonaInteres)
class ZonaInteresAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'usuario', 'latitud', 'longitud', 'radio_metros', 'activo']
    list_filter = ['activo', 'usuario']
    search_fields = ['nombre', 'descripcion', 'usuario__username']
    list_editable = ['activo']

