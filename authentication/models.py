from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver


class Empresa(models.Model):
    """
    Modelo para empresas en el sistema multi-tenant
    Basado en la estructura de EMPRESAS y EP
    """
    # Campos de la tabla EMPRESAS
    code = models.CharField(max_length=32, unique=True, help_text='Código interno legible')
    legal_name = models.TextField(help_text='Razón social')
    trade_name = models.TextField(null=True, blank=True, help_text='Nombre comercial')
    tax_id = models.CharField(max_length=32, null=True, blank=True, help_text='CUIT/IVA/etc.')
    country_id = models.SmallIntegerField(null=True, blank=True)
    type_id = models.SmallIntegerField(null=True, blank=True)
    email = models.CharField(max_length=120, null=True, blank=True)
    phone = models.CharField(max_length=40, null=True, blank=True)
    
    # Campos de la tabla EP (Empresa Proveedora)
    nombre = models.CharField(max_length=100, null=True, blank=True)
    fecha = models.DateTimeField(null=True, blank=True)
    status = models.SmallIntegerField(default=1, help_text='1=activa, 0=inactiva')
    
    # Campos de auditoría
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'authentication_empresa'
        verbose_name = 'Empresa'
        verbose_name_plural = 'Empresas'
        ordering = ['legal_name']
    
    def __str__(self):
        return self.legal_name or self.nombre or f"Empresa {self.id}"
    
    @property
    def activa(self):
        """Retorna True si la empresa está activa"""
        return self.status == 1


class Perfil(models.Model):
    """
    Perfiles del sistema - Define qué módulos/funcionalidades puede ver el usuario
    Ejemplos: Dashboard, Móviles, Equipos, Personas, Zonas, Reportes, Configuración
    """
    nombre = models.CharField(max_length=100, unique=True)
    codigo = models.CharField(max_length=50, unique=True)  # dashboard, moviles, equipos, etc.
    descripcion = models.TextField(null=True, blank=True)
    icono = models.CharField(max_length=50, null=True, blank=True)  # bi-speedometer2, bi-truck, etc.
    orden = models.IntegerField(default=0)  # Para ordenar en el menú
    activo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'perfiles'
        verbose_name = 'Perfil'
        verbose_name_plural = 'Perfiles'
        ordering = ['orden', 'nombre']
    
    def __str__(self):
        return self.nombre


class Rol(models.Model):
    """
    Roles del sistema - Define permisos sobre entidades específicas
    Ejemplos: Admin Total, Supervisor de Flota, Operador, Cliente, etc.
    """
    TIPO_EMPRESA_CHOICES = [
        ('EP', 'Empresa Proveedora'),
        ('ET', 'Empresa de Transporte/Cliente'),
        ('INTERNO', 'Usuario Interno del Sistema'),
    ]
    
    nombre = models.CharField(max_length=100, unique=True)
    codigo = models.CharField(max_length=50, unique=True)  # admin, supervisor, operador, etc.
    descripcion = models.TextField(null=True, blank=True)
    tipo_empresa = models.CharField(max_length=10, choices=TIPO_EMPRESA_CHOICES, default='INTERNO')
    
    # Perfiles a los que tiene acceso este rol
    perfiles = models.ManyToManyField(Perfil, related_name='roles', blank=True)
    
    # Permisos generales
    es_superusuario = models.BooleanField(default=False)  # Acceso total sin restricciones
    puede_crear = models.BooleanField(default=False)
    puede_editar = models.BooleanField(default=False)
    puede_eliminar = models.BooleanField(default=False)
    puede_ver_todo = models.BooleanField(default=False)  # Ver todos los registros o solo los propios
    
    activo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'roles'
        verbose_name = 'Rol'
        verbose_name_plural = 'Roles'
        ordering = ['nombre']
    
    def __str__(self):
        return f"{self.nombre} ({self.get_tipo_empresa_display()})"


class PermisoEntidad(models.Model):
    """
    Permisos específicos por entidad
    Define qué puede hacer un rol sobre cada entidad (móviles, equipos, personas, zonas, etc.)
    """
    ENTIDAD_CHOICES = [
        ('moviles', 'Móviles'),
        ('equipos', 'Equipos GPS'),
        ('personas', 'Personas/Conductores'),
        ('zonas', 'Zonas/Geocercas'),
        ('viajes', 'Viajes'),
        ('reportes', 'Reportes'),
        ('usuarios', 'Usuarios'),
        ('empresas', 'Empresas'),
    ]
    
    rol = models.ForeignKey(Rol, on_delete=models.CASCADE, related_name='permisos_entidad')
    entidad = models.CharField(max_length=50, choices=ENTIDAD_CHOICES)
    
    puede_ver = models.BooleanField(default=True)
    puede_crear = models.BooleanField(default=False)
    puede_editar = models.BooleanField(default=False)
    puede_eliminar = models.BooleanField(default=False)
    puede_exportar = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'permisos_entidad'
        verbose_name = 'Permiso de Entidad'
        verbose_name_plural = 'Permisos de Entidad'
        unique_together = ['rol', 'entidad']
    
    def __str__(self):
        return f"{self.rol.nombre} - {self.get_entidad_display()}"


class PerfilUsuario(models.Model):
    """
    Extensión del modelo User de Django con información adicional
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil_usuario')
    
    # Datos personales adicionales
    telefono = models.CharField(max_length=20, null=True, blank=True)
    documento = models.CharField(max_length=20, null=True, blank=True, verbose_name='DNI/Documento')
    
    # Rol y permisos
    rol = models.ForeignKey(Rol, on_delete=models.SET_NULL, null=True, blank=True, related_name='usuarios')
    perfiles_personalizados = models.ManyToManyField(
        Perfil, 
        related_name='usuarios', 
        blank=True,
        help_text='Perfiles adicionales específicos para este usuario (opcional)'
    )
    
    # Empresa (para futuro sistema multi-empresa)
    empresa = models.CharField(max_length=200, null=True, blank=True)
    empresa_id = models.IntegerField(null=True, blank=True, help_text='ID de la empresa (para futuro)')
    
    # 2FA (Two-Factor Authentication) - Para futuro
    two_factor_enabled = models.BooleanField(default=False, verbose_name='2FA Habilitado')
    two_factor_secret = models.CharField(max_length=100, null=True, blank=True)
    
    # Auditoría
    ultima_ip = models.GenericIPAddressField(null=True, blank=True)
    intentos_fallidos = models.IntegerField(default=0)
    bloqueado_hasta = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'perfil_usuario'
        verbose_name = 'Perfil de Usuario'
        verbose_name_plural = 'Perfiles de Usuario'
    
    def __str__(self):
        return f"Perfil de {self.user.username}"
    
    def tiene_perfil(self, codigo_perfil):
        """Verifica si el usuario tiene acceso a un perfil específico"""
        if self.user.is_superuser or (self.rol and self.rol.es_superusuario):
            return True
        
        if self.rol and self.rol.perfiles.filter(codigo=codigo_perfil, activo=True).exists():
            return True
        
        if self.perfiles_personalizados.filter(codigo=codigo_perfil, activo=True).exists():
            return True
        
        return False
    
    def puede_acceder_entidad(self, entidad, accion='ver'):
        """
        Verifica si el usuario puede realizar una acción sobre una entidad
        accion: 'ver', 'crear', 'editar', 'eliminar', 'exportar'
        """
        if self.user.is_superuser or (self.rol and self.rol.es_superusuario):
            return True
        
        if not self.rol:
            return False
        
        try:
            permiso = self.rol.permisos_entidad.get(entidad=entidad)
            if accion == 'ver':
                return permiso.puede_ver
            elif accion == 'crear':
                return permiso.puede_crear
            elif accion == 'editar':
                return permiso.puede_editar
            elif accion == 'eliminar':
                return permiso.puede_eliminar
            elif accion == 'exportar':
                return permiso.puede_exportar
        except PermisoEntidad.DoesNotExist:
            return False
        
        return False
    
    def esta_bloqueado(self):
        """Verifica si el usuario está bloqueado temporalmente"""
        if self.bloqueado_hasta and self.bloqueado_hasta > timezone.now():
            return True
        return False
    
    def registrar_intento_fallido(self):
        """Registra un intento fallido de login y bloquea si excede el límite"""
        self.intentos_fallidos += 1
        
        # Bloquear por 30 minutos después de 5 intentos fallidos
        if self.intentos_fallidos >= 5:
            self.bloqueado_hasta = timezone.now() + timezone.timedelta(minutes=30)
        
        self.save()
    
    def resetear_intentos_fallidos(self):
        """Resetea los intentos fallidos después de un login exitoso"""
        self.intentos_fallidos = 0
        self.bloqueado_hasta = None
        self.save()


class SesionUsuario(models.Model):
    """
    Registro de sesiones de usuario para auditoría y control
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sesiones')
    token = models.CharField(max_length=500, unique=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(null=True, blank=True)
    
    fecha_inicio = models.DateTimeField(auto_now_add=True)
    fecha_ultimo_acceso = models.DateTimeField(auto_now=True)
    fecha_fin = models.DateTimeField(null=True, blank=True)
    
    activa = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'sesiones_usuario'
        verbose_name = 'Sesión de Usuario'
        verbose_name_plural = 'Sesiones de Usuario'
        ordering = ['-fecha_inicio']
    
    def __str__(self):
        return f"{self.user.username} - {self.fecha_inicio}"


# Signals para crear automáticamente PerfilUsuario al crear un User
@receiver(post_save, sender=User)
def crear_perfil_usuario(sender, instance, created, **kwargs):
    """Crea automáticamente un PerfilUsuario cuando se crea un User"""
    if created:
        PerfilUsuario.objects.create(user=instance)


@receiver(post_save, sender=User)
def guardar_perfil_usuario(sender, instance, **kwargs):
    """Guarda el PerfilUsuario cuando se guarda el User"""
    if hasattr(instance, 'perfil_usuario'):
        instance.perfil_usuario.save()
