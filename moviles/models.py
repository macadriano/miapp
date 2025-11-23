from django.contrib.gis.db import models
from django.contrib.gis.db import models as gis_models
from django.utils import timezone


class Movil(models.Model):
    """
    Modelo de Móviles - NUEVA ESTRUCTURA OPTIMIZADA
    Solo contiene datos estáticos del vehículo
    Los datos dinámicos están en moviles_status, moviles_geocode y posiciones
    """
    # Identificación
    id = models.BigAutoField(primary_key=True)
    codigo = models.CharField(max_length=32, unique=True, null=True, blank=True)
    alias = models.CharField(max_length=100, null=True, blank=True)
    patente = models.CharField(max_length=20, unique=True, null=True, blank=True)
    vin = models.CharField(max_length=17, null=True, blank=True)

    # Datos del vehículo
    marca = models.TextField(null=True, blank=True)
    modelo = models.TextField(null=True, blank=True)
    anio = models.SmallIntegerField(null=True, blank=True)
    color = models.TextField(null=True, blank=True)
    tipo_vehiculo = models.CharField(max_length=20, null=True, blank=True)

    # Equipo GPS
    gps_id = models.CharField(max_length=50, unique=True, null=True, blank=True)

    # Estado
    activo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'moviles'
        verbose_name = 'Móvil'
        verbose_name_plural = 'Móviles'

    def __str__(self):
        return f"{self.alias or self.patente or self.gps_id}"
    
    def get_equipo_gps(self):
        """Retorna el equipo GPS asignado a este móvil (por gps_id/IMEI)"""
        if self.gps_id:
            try:
                from django.apps import apps
                Equipo = apps.get_model('gps', 'Equipo')
                return Equipo.objects.get(imei=self.gps_id)
            except Exception:
                return None
        return None


class MovilStatus(models.Model):
    """
    Datos dinámicos de última posición de cada móvil
    Relación 1:1 con moviles
    """
    
    # Relación con móvil
    movil = models.OneToOneField(
        Movil, 
        on_delete=models.CASCADE, 
        related_name='status',
        primary_key=True
    )
    
    # Posición GPS
    ultimo_lat = models.DecimalField(max_digits=10, decimal_places=6, null=True, blank=True)
    ultimo_lon = models.DecimalField(max_digits=10, decimal_places=6, null=True, blank=True)
    ultima_altitud = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    
    # Datos de movimiento
    ultima_velocidad_kmh = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    ultimo_rumbo = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    # Datos del equipo GPS
    satelites = models.SmallIntegerField(null=True, blank=True)
    hdop = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    calidad_senal = models.SmallIntegerField(null=True, blank=True)
    
    # Estado del vehículo
    ignicion = models.BooleanField(default=False)
    bateria_pct = models.SmallIntegerField(null=True, blank=True)
    odometro_km = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Estado de conexión
    estado_conexion = models.CharField(
        max_length=20,
        choices=[
            ('conectado', 'Conectado'),
            ('desconectado', 'Desconectado'),
            ('error', 'Error'),
        ],
        default='desconectado'
    )
    
    # Timestamps
    fecha_gps = models.DateTimeField(null=True, blank=True)
    fecha_recepcion = models.DateTimeField(null=True, blank=True)
    ultima_actualizacion = models.DateTimeField(auto_now=True)
    
    # Referencia a última posición en histórico
    id_ultima_posicion = models.BigIntegerField(null=True, blank=True)
    
    # Datos crudos
    raw_data = models.TextField(null=True, blank=True)
    raw_json = models.JSONField(null=True, blank=True)
    
    class Meta:
        db_table = 'moviles_status'
        verbose_name = 'Estado de Móvil'
        verbose_name_plural = 'Estados de Móviles'
        indexes = [
            models.Index(fields=['estado_conexion']),
            models.Index(fields=['fecha_gps']),
            models.Index(fields=['ultima_actualizacion']),
        ]
    
    def __str__(self):
        return f"Estado de {self.movil}"


class MovilGeocode(models.Model):
    """
    Última geocodificación de cada móvil
    Relación 1:1 con moviles
    """
    
    # Relación con móvil
    movil = models.OneToOneField(
        Movil, 
        on_delete=models.CASCADE, 
        related_name='geocode',
        primary_key=True
    )
    
    # Dirección formateada
    direccion_formateada = models.TextField(null=True, blank=True)
    
    # Componentes de dirección
    calle = models.CharField(max_length=200, null=True, blank=True)
    numero = models.CharField(max_length=20, null=True, blank=True)
    piso = models.CharField(max_length=20, null=True, blank=True)
    depto = models.CharField(max_length=20, null=True, blank=True)
    barrio = models.CharField(max_length=100, null=True, blank=True)
    localidad = models.CharField(max_length=100, null=True, blank=True)
    municipio = models.CharField(max_length=100, null=True, blank=True)
    provincia = models.CharField(max_length=100, null=True, blank=True)
    codigo_postal = models.CharField(max_length=20, null=True, blank=True)
    pais = models.CharField(max_length=100, default='Argentina')
    
    # Metadatos de geocodificación
    fuente_geocodificacion = models.CharField(max_length=50, null=True, blank=True)
    confianza_geocodificacion = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True)
    geohash = models.CharField(max_length=20, null=True, blank=True)
    
    # Timestamps
    fecha_geocodificacion = models.DateTimeField(null=True, blank=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'moviles_geocode'
        verbose_name = 'Geocodificación de Móvil'
        verbose_name_plural = 'Geocodificaciones de Móviles'
        indexes = [
            models.Index(fields=['provincia', 'localidad']),
            models.Index(fields=['fecha_geocodificacion']),
        ]
    
    def __str__(self):
        return f"Geocodificación de {self.movil}"


class MovilObservacion(models.Model):
    """
    Observaciones y notas de cada móvil
    Relación 1:N con moviles
    """
    
    # Relación con móvil
    movil = models.ForeignKey(
        Movil, 
        on_delete=models.CASCADE, 
        related_name='observaciones'
    )
    
    # Contenido de la observación
    titulo = models.CharField(max_length=200)
    contenido = models.TextField()
    
    # Categorización
    categoria = models.CharField(
        max_length=50,
        choices=[
            ('general', 'General'),
            ('mantenimiento', 'Mantenimiento'),
            ('incidente', 'Incidente'),
            ('documentacion', 'Documentación'),
            ('reparacion', 'Reparación'),
            ('inspeccion', 'Inspección'),
        ],
        default='general'
    )
    
    # Prioridad
    prioridad = models.CharField(
        max_length=20,
        choices=[
            ('baja', 'Baja'),
            ('media', 'Media'),
            ('alta', 'Alta'),
            ('urgente', 'Urgente'),
        ],
        default='media'
    )
    
    # Estado de la observación
    estado = models.CharField(
        max_length=20,
        choices=[
            ('abierta', 'Abierta'),
            ('en_proceso', 'En Proceso'),
            ('cerrada', 'Cerrada'),
            ('cancelada', 'Cancelada'),
        ],
        default='abierta'
    )
    
    # Timestamps y auditoría
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    fecha_vencimiento = models.DateTimeField(null=True, blank=True)
    
    # Usuario que creó la observación
    usuario_creacion = models.ForeignKey(
        'auth.User', 
        on_delete=models.SET_NULL, 
        null=True,
        related_name='observaciones_creadas'
    )
    
    # Usuario asignado (opcional)
    usuario_asignado = models.ForeignKey(
        'auth.User', 
        on_delete=models.SET_NULL, 
        null=True,
        blank=True,
        related_name='observaciones_asignadas'
    )
    
    class Meta:
        db_table = 'moviles_observaciones'
        verbose_name = 'Observación de Móvil'
        verbose_name_plural = 'Observaciones de Móviles'
        ordering = ['-fecha_creacion']
        indexes = [
            models.Index(fields=['movil', 'fecha_creacion']),
            models.Index(fields=['categoria']),
            models.Index(fields=['estado']),
            models.Index(fields=['prioridad']),
        ]
    
    def __str__(self):
        return f"{self.movil} - {self.titulo}"


class MovilFoto(models.Model):
    """
    Fotos de cada móvil
    Relación 1:N con moviles
    """
    
    # Relación con móvil
    movil = models.ForeignKey(
        Movil, 
        on_delete=models.CASCADE, 
        related_name='fotos'
    )
    
    # Archivo de imagen
    imagen = models.ImageField(
        upload_to='moviles/fotos/%Y/%m/',
        help_text="Imagen del móvil"
    )
    
    # Metadatos de la imagen
    titulo = models.CharField(max_length=200, blank=True)
    descripcion = models.TextField(blank=True)
    
    # Categorización
    categoria = models.CharField(
        max_length=50,
        choices=[
            ('exterior', 'Exterior'),
            ('interior', 'Interior'),
            ('documentos', 'Documentos'),
            ('danos', 'Daños'),
            ('mantenimiento', 'Mantenimiento'),
            ('accesorios', 'Accesorios'),
            ('general', 'General'),
        ],
        default='general'
    )
    
    # Información técnica
    tamaño_archivo = models.IntegerField(null=True, blank=True, help_text="Tamaño en bytes")
    dimensiones = models.CharField(max_length=20, blank=True, help_text="Ancho x Alto en píxeles")
    
    # Geolocalización de la foto (opcional)
    latitud = models.DecimalField(max_digits=10, decimal_places=6, null=True, blank=True)
    longitud = models.DecimalField(max_digits=10, decimal_places=6, null=True, blank=True)
    
    # Orden y visibilidad
    orden = models.IntegerField(default=0, help_text="Orden de visualización")
    es_principal = models.BooleanField(default=False, help_text="Foto principal del móvil")
    visible = models.BooleanField(default=True)
    
    # Timestamps y auditoría
    fecha_captura = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    # Usuario que subió la foto
    usuario_captura = models.ForeignKey(
        'auth.User', 
        on_delete=models.SET_NULL, 
        null=True,
        related_name='fotos_capturadas'
    )
    
    # Relación opcional con observación
    observacion = models.ForeignKey(
        MovilObservacion,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='fotos'
    )
    
    class Meta:
        db_table = 'moviles_fotos'
        verbose_name = 'Foto de Móvil'
        verbose_name_plural = 'Fotos de Móviles'
        ordering = ['orden', '-fecha_captura']
        indexes = [
            models.Index(fields=['movil', 'orden']),
            models.Index(fields=['categoria']),
            models.Index(fields=['es_principal']),
            models.Index(fields=['fecha_captura']),
        ]
        constraints = [
            # Solo una foto principal por móvil
            models.UniqueConstraint(
                fields=['movil'],
                condition=models.Q(es_principal=True),
                name='unique_foto_principal_por_movil'
            ),
        ]
    
    def __str__(self):
        return f"{self.movil} - {self.titulo or 'Foto'}"


class MovilNota(models.Model):
    """
    Notas generales de cada móvil (campo de texto libre)
    Relación 1:1 con moviles
    """
    
    # Relación con móvil
    movil = models.OneToOneField(
        Movil, 
        on_delete=models.CASCADE, 
        related_name='nota_general',
        primary_key=True
    )
    
    # Contenido de la nota
    contenido = models.TextField(
        blank=True,
        help_text="Notas generales sobre el móvil"
    )
    
    # Timestamps
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    # Usuario que actualizó la nota
    usuario_actualizacion = models.ForeignKey(
        'auth.User', 
        on_delete=models.SET_NULL, 
        null=True
    )
    
    class Meta:
        db_table = 'moviles_notas'
        verbose_name = 'Nota de Móvil'
        verbose_name_plural = 'Notas de Móviles'
    
    def __str__(self):
        return f"Nota de {self.movil}"
