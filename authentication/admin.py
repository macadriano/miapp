from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import Rol, Perfil, PermisoEntidad, SesionUsuario, PerfilUsuario


@admin.register(Perfil)
class PerfilAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'codigo', 'orden', 'activo', 'created_at']
    list_filter = ['activo']
    search_fields = ['nombre', 'codigo', 'descripcion']
    ordering = ['orden', 'nombre']


class PermisoEntidadInline(admin.TabularInline):
    model = PermisoEntidad
    extra = 1


@admin.register(Rol)
class RolAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'codigo', 'tipo_empresa', 'es_superusuario', 'activo', 'created_at']
    list_filter = ['tipo_empresa', 'es_superusuario', 'activo']
    search_fields = ['nombre', 'codigo', 'descripcion']
    filter_horizontal = ['perfiles']
    inlines = [PermisoEntidadInline]
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('nombre', 'codigo', 'descripcion', 'tipo_empresa')
        }),
        ('Perfiles de Acceso', {
            'fields': ('perfiles',)
        }),
        ('Permisos Generales', {
            'fields': ('es_superusuario', 'puede_crear', 'puede_editar', 'puede_eliminar', 'puede_ver_todo')
        }),
        ('Estado', {
            'fields': ('activo',)
        }),
    )


@admin.register(PermisoEntidad)
class PermisoEntidadAdmin(admin.ModelAdmin):
    list_display = ['rol', 'entidad', 'puede_ver', 'puede_crear', 'puede_editar', 'puede_eliminar', 'puede_exportar']
    list_filter = ['entidad', 'rol']
    search_fields = ['rol__nombre', 'entidad']


class PerfilUsuarioInline(admin.StackedInline):
    model = PerfilUsuario
    can_delete = False
    verbose_name_plural = 'Perfil de Usuario'
    filter_horizontal = ['perfiles_personalizados']
    
    fieldsets = (
        ('Información Adicional', {
            'fields': ('telefono', 'documento')
        }),
        ('Rol y Permisos', {
            'fields': ('rol', 'perfiles_personalizados')
        }),
        ('Empresa', {
            'fields': ('empresa', 'empresa_id'),
            'classes': ('collapse',)
        }),
        ('2FA', {
            'fields': ('two_factor_enabled', 'two_factor_secret'),
            'classes': ('collapse',)
        }),
        ('Seguridad', {
            'fields': ('intentos_fallidos', 'bloqueado_hasta', 'ultima_ip')
        }),
    )


# Extender el UserAdmin de Django
class CustomUserAdmin(BaseUserAdmin):
    inlines = (PerfilUsuarioInline,)
    list_display = ['username', 'email', 'first_name', 'last_name', 'get_rol', 'is_active', 'is_staff', 'date_joined']
    list_filter = ['is_active', 'is_staff', 'is_superuser', 'date_joined']
    
    def get_rol(self, obj):
        if hasattr(obj, 'perfil_usuario') and obj.perfil_usuario.rol:
            return obj.perfil_usuario.rol.nombre
        return '-'
    get_rol.short_description = 'Rol'


# Desregistrar el UserAdmin original y registrar el personalizado
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)


@admin.register(SesionUsuario)
class SesionUsuarioAdmin(admin.ModelAdmin):
    list_display = ['user', 'ip_address', 'fecha_inicio', 'fecha_ultimo_acceso', 'activa']
    list_filter = ['activa', 'fecha_inicio']
    search_fields = ['user__username', 'user__email', 'ip_address']
    readonly_fields = ['token', 'fecha_inicio', 'fecha_ultimo_acceso']
    ordering = ['-fecha_inicio']
