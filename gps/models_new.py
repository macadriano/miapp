"""
Nuevos modelos Django para la arquitectura GPS en tiempo real
Basados en la estructura propuesta en el Excel

ESTRUCTURA NUEVA:
- moviles: Datos estáticos del vehículo
- moviles_status: Datos dinámicos de última posición (1:1 con moviles)
- moviles_geocode: Última geocodificación (1:1 con moviles)
- posiciones: Histórico de posiciones (1:N con moviles)
- cat_moviles: Catálogo específico del esquema moviles
- flotas: Descripción de agrupaciones de móviles
- flota_movil: Relación entre móviles y flotas
"""

from django.db import models
from django.contrib.gis.db import models as gis_models
from django.utils import timezone

class Movil(models.Model):
    """
    Tabla principal de móviles - Datos estáticos del vehículo
    Relación 1:1 con moviles_status y moviles_geocode
    """
    
    # Identificación
    id = models.BigAutoField(primary_key=True)
    codigo = models.CharField(max_length=50, null=True, blank=True, unique=True)
    alias = models.CharField(max_length=100, null=True, blank=True)
    patente = models.CharField(max_length=20, null=True, blank=True, unique=True)
    vin = models.CharField(max_length=17, null=True, blank=True)
    
    # Datos del vehículo
    marca = models.CharField(max_length=100, null=True, blank=True)
    modelo = models.CharField(max_length=100, null=True, blank=True)
    anio = models.SmallIntegerField(null=True, blank=True)
    color = models.CharField(max_length=50, null=True, blank=True)
    tipo_vehiculo = models.CharField(max_length=50, null=True, blank=True)
    
    # Equipo GPS
    gps_id = models.CharField(max_length=20, null=True, blank=True, help_text="IMEI del equipo GPS")
    
    # Estado
    activo = models.BooleanField(default=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'moviles'
        verbose_name = 'Móvil'
        verbose_name_plural = 'Móviles'
        ordering = ['patente']
        indexes = [
            models.Index(fields=['gps_id']),
            models.Index(fields=['patente']),
            models.Index(fields=['activo']),
        ]
    
    def __str__(self):
        return self.patente or self.alias or f"Móvil {self.id}"


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


class Posicion(models.Model):
    """
    Histórico de posiciones GPS
    Relación 1:N con moviles
    """
    
    # Relación con móvil
    movil = models.ForeignKey(
        Movil, 
        on_delete=models.CASCADE, 
        related_name='posiciones'
    )
    
    # Posición GPS
    latitud = models.DecimalField(max_digits=10, decimal_places=6)
    longitud = models.DecimalField(max_digits=10, decimal_places=6)
    altitud = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    
    # Datos de movimiento
    velocidad_kmh = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    rumbo = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    # Datos del equipo GPS
    satelites = models.SmallIntegerField(null=True, blank=True)
    hdop = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    calidad_senal = models.SmallIntegerField(null=True, blank=True)
    
    # Estado del vehículo
    ignicion = models.BooleanField(default=False)
    bateria_pct = models.SmallIntegerField(null=True, blank=True)
    odometro_km = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Timestamps
    fecha_gps = models.DateTimeField()
    fecha_recepcion = models.DateTimeField(auto_now_add=True)
    
    # Calidad del dato
    calidad_datos = models.CharField(
        max_length=20,
        choices=[
            ('excelente', 'Excelente'),
            ('buena', 'Buena'),
            ('regular', 'Regular'),
            ('mala', 'Mala'),
        ],
        default='buena'
    )
    
    # Datos crudos
    raw_data = models.TextField(null=True, blank=True)
    raw_json = models.JSONField(null=True, blank=True)
    
    # Geometría PostGIS
    geom = gis_models.PointField(null=True, blank=True, srid=4326)
    
    class Meta:
        db_table = 'posiciones'
        verbose_name = 'Posición'
        verbose_name_plural = 'Posiciones'
        ordering = ['-fecha_gps']
        indexes = [
            models.Index(fields=['movil', 'fecha_gps']),
            models.Index(fields=['fecha_gps']),
            models.Index(fields=['calidad_datos']),
        ]
    
    def __str__(self):
        return f"Posición de {self.movil} - {self.fecha_gps}"


class CatMovil(models.Model):
    """
    Catálogo específico del esquema móviles
    """
    
    codigo = models.CharField(max_length=50, unique=True)
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(null=True, blank=True)
    activo = models.BooleanField(default=True)
    
    # Metadatos
    orden = models.IntegerField(default=0)
    color_hex = models.CharField(max_length=7, null=True, blank=True)
    icono = models.CharField(max_length=100, null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'cat_moviles'
        verbose_name = 'Catálogo de Móvil'
        verbose_name_plural = 'Catálogos de Móviles'
        ordering = ['orden', 'nombre']
    
    def __str__(self):
        return self.nombre


class Flota(models.Model):
    """
    Descripción de agrupaciones de móviles
    """
    
    codigo = models.CharField(max_length=50, unique=True)
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(null=True, blank=True)
    
    # Configuración visual
    color_hex = models.CharField(max_length=7, null=True, blank=True)
    icono = models.CharField(max_length=100, null=True, blank=True)
    
    # Estado
    activa = models.BooleanField(default=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'flotas'
        verbose_name = 'Flota'
        verbose_name_plural = 'Flotas'
        ordering = ['nombre']
    
    def __str__(self):
        return self.nombre


class FlotaMovil(models.Model):
    """
    Relación entre móviles y flotas
    """
    
    flota = models.ForeignKey(Flota, on_delete=models.CASCADE, related_name='moviles')
    movil = models.ForeignKey(Movil, on_delete=models.CASCADE, related_name='flotas')
    
    # Metadatos de la relación
    fecha_asignacion = models.DateTimeField(auto_now_add=True)
    activa = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'flota_movil'
        verbose_name = 'Flota-Móvil'
        verbose_name_plural = 'Flotas-Móviles'
        unique_together = ['flota', 'movil']
        indexes = [
            models.Index(fields=['flota', 'activa']),
            models.Index(fields=['movil', 'activa']),
        ]
    
    def __str__(self):
        return f"{self.flota} - {self.movil}"


# Modelos para receptores GPS (nueva funcionalidad)
class TipoEquipoGPS(models.Model):
    """
    Tipos de equipos GPS soportados
    """
    
    codigo = models.CharField(max_length=20, unique=True)
    nombre = models.CharField(max_length=100)
    fabricante = models.CharField(max_length=100)
    protocolo = models.CharField(
        max_length=10,
        choices=[
            ('TCP', 'TCP'),
            ('UDP', 'UDP'),
            ('HTTP', 'HTTP'),
        ]
    )
    puerto_default = models.IntegerField()
    formato_datos = models.JSONField(help_text="Especificación del formato de datos")
    activo = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'tipos_equipos_gps'
        verbose_name = 'Tipo de Equipo GPS'
        verbose_name_plural = 'Tipos de Equipos GPS'
    
    def __str__(self):
        return f"{self.fabricante} - {self.nombre}"


class ConfiguracionReceptor(models.Model):
    """
    Configuración de receptores de datos GPS
    """
    
    nombre = models.CharField(max_length=100)
    tipo_equipo = models.ForeignKey(TipoEquipoGPS, on_delete=models.CASCADE)
    puerto = models.IntegerField(unique=True)
    protocolo = models.CharField(max_length=10)
    activo = models.BooleanField(default=True)
    max_conexiones = models.IntegerField(default=100)
    max_equipos = models.IntegerField(default=1000)
    timeout = models.IntegerField(default=30)
    region = models.CharField(max_length=50, blank=True)
    prioridad = models.IntegerField(default=1)
    configuracion_avanzada = models.JSONField(null=True, blank=True)
    
    class Meta:
        db_table = 'configuraciones_receptores'
        verbose_name = 'Configuración de Receptor'
        verbose_name_plural = 'Configuraciones de Receptores'
    
    def __str__(self):
        return f"{self.nombre} - Puerto {self.puerto}"


class EstadisticasRecepcion(models.Model):
    """
    Estadísticas de recepción de datos GPS
    """
    
    receptor = models.ForeignKey(ConfiguracionReceptor, on_delete=models.CASCADE)
    fecha = models.DateField()
    equipos_conectados = models.IntegerField(default=0)
    datos_recibidos = models.IntegerField(default=0)
    datos_procesados = models.IntegerField(default=0)
    errores = models.IntegerField(default=0)
    latencia_promedio = models.DecimalField(max_digits=8, decimal_places=3, null=True)
    
    class Meta:
        db_table = 'estadisticas_recepcion'
        unique_together = ('receptor', 'fecha')
        verbose_name = 'Estadística de Recepción'
        verbose_name_plural = 'Estadísticas de Recepción'
    
    def __str__(self):
        return f"{self.receptor} - {self.fecha}"


# Mantener modelos existentes para compatibilidad
class Equipo(models.Model):
    """
    Modelo de Equipos GPS (mantener para compatibilidad)
    """
    id = models.BigAutoField(primary_key=True)
    imei = models.CharField(max_length=15, unique=True, verbose_name='IMEI')
    numero_serie = models.CharField(max_length=50, null=True, blank=True, verbose_name='Número de Serie')
    marca = models.CharField(max_length=50, null=True, blank=True)
    modelo = models.CharField(max_length=50, null=True, blank=True)
    estado = models.CharField(max_length=20, null=True, blank=True)
    empresa = models.ForeignKey(
        'Empresa',
        on_delete=models.DO_NOTHING,
        null=True,
        blank=True
    )
    fecha_instalacion = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    
    class Meta:
        managed = False
        db_table = 'equipos_gps'
        verbose_name = 'Equipo GPS'
        verbose_name_plural = 'Equipos GPS'
    
    def __str__(self):
        return f"{self.imei} - {self.marca or 'Sin marca'} {self.modelo or ''}"


class Empresa(models.Model):
    """Modelo temporal para la relación"""
    id = models.BigAutoField(primary_key=True)
    nombre = models.CharField(max_length=200)
    
    class Meta:
        managed = False
        db_table = 'empresas'
