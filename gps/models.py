from django.contrib.gis.db import models
from django.contrib.gis.db import models as gis_models
from django.utils import timezone
#from django.contrib.postgres.fields import CITextField


# class Movil(models.Model):  # MOVIDO A moviles/models.py
#     """
#     Modelo de Móviles - NUEVA ESTRUCTURA OPTIMIZADA
#     Solo contiene datos estáticos del vehículo
#     Los datos dinámicos están en moviles_status, moviles_geocode y posiciones
#     """
#     # Identificación
#     id = models.BigAutoField(primary_key=True)
#     codigo = models.CharField(max_length=32, unique=True, null=True, blank=True)
#     alias = models.CharField(max_length=100, null=True, blank=True)
#     patente = models.CharField(max_length=20, unique=True, null=True, blank=True)
#     vin = models.CharField(max_length=17, null=True, blank=True)
#
#     # Datos del vehículo
#     marca = models.TextField(null=True, blank=True)
#     modelo = models.TextField(null=True, blank=True)
#     anio = models.SmallIntegerField(null=True, blank=True)
#     color = models.TextField(null=True, blank=True)
#     tipo_vehiculo = models.CharField(max_length=20, null=True, blank=True)
#
#     # Equipo GPS
#     gps_id = models.CharField(max_length=50, unique=True, null=True, blank=True)
#
#     # Estado
#     activo = models.BooleanField(default=True)
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)
#
#     class Meta:
#         db_table = 'moviles'
#         verbose_name = 'Móvil'
#         verbose_name_plural = 'Móviles'
#
#     def __str__(self):
#         return f"{self.alias or self.patente or self.gps_id}"
#     
#     def get_equipo_gps(self):
#         """Retorna el equipo GPS asignado a este móvil (por gps_id/IMEI)"""
#         if self.gps_id:
#             try:
#                 # Usar una importación más simple para evitar problemas circulares
#                 Equipo = self.__class__.objects.model._meta.apps.get_model('gps', 'Equipo')
#                 return Equipo.objects.get(imei=self.gps_id)
#             except Exception:
#                 return None
#         return None


class Equipo(models.Model):
    """
    Modelo de Equipos GPS - TABLA EXISTENTE
    Representa los dispositivos GPS que se instalan en los vehículos
    La relación con móviles es a través del campo gps_id (IMEI)
    """
    # Identificación
    id = models.BigAutoField(primary_key=True)
    imei = models.CharField(max_length=15, unique=True, verbose_name='IMEI')
    numero_serie = models.CharField(max_length=50, null=True, blank=True, verbose_name='Número de Serie')
    
    # Información del equipo
    marca = models.CharField(max_length=50, null=True, blank=True)
    modelo = models.CharField(max_length=50, null=True, blank=True)
    
    # Estado
    estado = models.CharField(max_length=20, null=True, blank=True)
    
    # Relación con empresa (para futuro)
    empresa = models.ForeignKey(
        'Empresa',
        on_delete=models.DO_NOTHING,
        null=True,
        blank=True
        # La columna en la BD se llama 'empresa_id' (convención de Django)
    )
    
    # Fechas
    fecha_instalacion = models.DateTimeField(null=True, blank=True)
    
    # Auditoría
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        managed = True  # Permitir que Django gestione la tabla
        db_table = 'equipos_gps'
        verbose_name = 'Equipo GPS'
        verbose_name_plural = 'Equipos GPS'
    
    def __str__(self):
        return f"{self.imei} - {self.marca or 'Sin marca'} {self.modelo or ''}"
    
    def get_movil_asignado(self):
        """Retorna el móvil asignado a este equipo (por IMEI)"""
        try:
            from django.apps import apps
            Movil = apps.get_model('moviles', 'Movil')
            return Movil.objects.get(gps_id=self.imei)
        except Exception:
            return None


class Empresa(models.Model):
    """Modelo temporal para la relación (se creará completo en el futuro)"""
    id = models.BigAutoField(primary_key=True)
    nombre = models.CharField(max_length=200)
    
    class Meta:
        managed = False
        db_table = 'empresas'


# Nuevos modelos para la estructura optimizada
# class MovilStatus(models.Model):  # MOVIDO A moviles/models.py
#     """
#     Datos dinámicos de última posición de cada móvil
#     Relación 1:1 con moviles
#     """
#     
#     # Relación con móvil
#     movil = models.OneToOneField(
#         Movil, 
#         on_delete=models.CASCADE, 
#         related_name='status',
#         primary_key=True
#     )
#     
#     # Posición GPS
#     ultimo_lat = models.DecimalField(max_digits=10, decimal_places=6, null=True, blank=True)
#     ultimo_lon = models.DecimalField(max_digits=10, decimal_places=6, null=True, blank=True)
#     ultima_altitud = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
#     
#     # Datos de movimiento
#     ultima_velocidad_kmh = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
#     ultimo_rumbo = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
#     
#     # Datos del equipo GPS
#     satelites = models.SmallIntegerField(null=True, blank=True)
#     hdop = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
#     calidad_senal = models.SmallIntegerField(null=True, blank=True)
#     
#     # Estado del vehículo
#     ignicion = models.BooleanField(default=False)
#     bateria_pct = models.SmallIntegerField(null=True, blank=True)
#     odometro_km = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
#     
#     # Estado de conexión
#     estado_conexion = models.CharField(
#         max_length=20,
#         choices=[
#             ('conectado', 'Conectado'),
#             ('desconectado', 'Desconectado'),
#             ('error', 'Error'),
#         ],
#         default='desconectado'
#     )
#     
#     # Timestamps
#     fecha_gps = models.DateTimeField(null=True, blank=True)
#     fecha_recepcion = models.DateTimeField(null=True, blank=True)
#     ultima_actualizacion = models.DateTimeField(auto_now=True)
#     
#     # Referencia a última posición en histórico
#     id_ultima_posicion = models.BigIntegerField(null=True, blank=True)
#     
#     # Datos crudos
#     raw_data = models.TextField(null=True, blank=True)
#     raw_json = models.JSONField(null=True, blank=True)
#     
#     class Meta:
#         db_table = 'moviles_status'
#         verbose_name = 'Estado de Móvil'
#         verbose_name_plural = 'Estados de Móviles'
#         indexes = [
#             models.Index(fields=['estado_conexion']),
#             models.Index(fields=['fecha_gps']),
#             models.Index(fields=['ultima_actualizacion']),
#         ]
#     
#     def __str__(self):
#         return f"Estado de {self.movil}"


# class MovilGeocode(models.Model):  # MOVIDO A moviles/models.py
#     """
#     Última geocodificación de cada móvil
#     Relación 1:1 con moviles
#     """
#     
#     # Relación con móvil
#     movil = models.OneToOneField(
#         Movil, 
#         on_delete=models.CASCADE, 
#         related_name='geocode',
#         primary_key=True
#     )
#     
#     # Dirección formateada
#     direccion_formateada = models.TextField(null=True, blank=True)
#     
#     # Componentes de dirección
#     calle = models.CharField(max_length=200, null=True, blank=True)
#     numero = models.CharField(max_length=20, null=True, blank=True)
#     piso = models.CharField(max_length=20, null=True, blank=True)
#     depto = models.CharField(max_length=20, null=True, blank=True)
#     barrio = models.CharField(max_length=100, null=True, blank=True)
#     localidad = models.CharField(max_length=100, null=True, blank=True)
#     municipio = models.CharField(max_length=100, null=True, blank=True)
#     provincia = models.CharField(max_length=100, null=True, blank=True)
#     codigo_postal = models.CharField(max_length=20, null=True, blank=True)
#     pais = models.CharField(max_length=100, default='Argentina')
#     
#     # Metadatos de geocodificación
#     fuente_geocodificacion = models.CharField(max_length=50, null=True, blank=True)
#     confianza_geocodificacion = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True)
#     geohash = models.CharField(max_length=20, null=True, blank=True)
#     
#     # Timestamps
#     fecha_geocodificacion = models.DateTimeField(null=True, blank=True)
#     fecha_actualizacion = models.DateTimeField(auto_now=True)
#     
#     class Meta:
#         db_table = 'moviles_geocode'
#         verbose_name = 'Geocodificación de Móvil'
#         verbose_name_plural = 'Geocodificaciones de Móviles'
#         indexes = [
#             models.Index(fields=['provincia', 'localidad']),
#             models.Index(fields=['fecha_geocodificacion']),
#         ]
#     
#     def __str__(self):
#         return f"Geocodificación de {self.movil}"


# class Posicion(models.Model):  # COMENTADO - DEFINICIÓN DUPLICADA
#     """
#     Histórico de posiciones GPS
#     Relación 1:N con moviles
#     """
#     
#     # Relación con móvil
#     movil = models.ForeignKey(
#         Movil, 
#         on_delete=models.CASCADE, 
#         related_name='posiciones'
#     )
#     
#     # Posición GPS
#     latitud = models.DecimalField(max_digits=10, decimal_places=6)
#     longitud = models.DecimalField(max_digits=10, decimal_places=6)
#     altitud = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
#     
#     # Datos de movimiento
#     velocidad_kmh = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
#     rumbo = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
#     
#     # Datos del equipo GPS
#     satelites = models.SmallIntegerField(null=True, blank=True)
#     hdop = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
#     calidad_senal = models.SmallIntegerField(null=True, blank=True)
#     
#     # Estado del vehículo
#     ignicion = models.BooleanField(default=False)
#     bateria_pct = models.SmallIntegerField(null=True, blank=True)
#     odometro_km = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
#     
#     # Timestamps
#     fecha_gps = models.DateTimeField()
#     fecha_recepcion = models.DateTimeField(auto_now_add=True)
#     
#     # Calidad del dato
#     calidad_datos = models.CharField(
#         max_length=20,
#         choices=[
#             ('excelente', 'Excelente'),
#             ('buena', 'Buena'),
#             ('regular', 'Regular'),
#             ('mala', 'Mala'),
#         ],
#         default='buena'
#     )
#     
#     # Datos crudos
#     raw_data = models.TextField(null=True, blank=True)
#     raw_json = models.JSONField(null=True, blank=True)
#     
#     # Geometría PostGIS
#     geom = gis_models.PointField(null=True, blank=True, srid=4326)
#     
#     class Meta:
# #         db_table = 'posiciones'  # COMENTADO - CONFLICTO CON OTRA DEFINICIÓN
#         verbose_name = 'Posición'
#         verbose_name_plural = 'Posiciones'
#         ordering = ['-fecha_gps']
#         indexes = [
#             models.Index(fields=['movil', 'fecha_gps']),
#             models.Index(fields=['fecha_gps']),
#             models.Index(fields=['calidad_datos']),
#         ]
#     
#     def __str__(self):
#         return f"Posición de {self.movil} - {self.fecha_gps}"


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
    transporte = models.CharField(
        max_length=10,
        choices=[
            ('TCP', 'TCP'),
            ('UDP', 'UDP'),
            ('HTTP', 'HTTP'),
        ],
        default='TCP'
    )
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


# class MovilObservacion(models.Model):  # MOVIDO A moviles/models.py
#     """
#     Observaciones y notas de cada móvil
#     Relación 1:N con moviles
#     """
#     
#     # Relación con móvil
#     movil = models.ForeignKey(
#         Movil, 
#         on_delete=models.CASCADE, 
#         related_name='observaciones'
#     )
#     
#     # Contenido de la observación
#     titulo = models.CharField(max_length=200)
#     contenido = models.TextField()
#     
#     # Categorización
#     categoria = models.CharField(
#         max_length=50,
#         choices=[
#             ('general', 'General'),
#             ('mantenimiento', 'Mantenimiento'),
#             ('incidente', 'Incidente'),
#             ('documentacion', 'Documentación'),
#             ('reparacion', 'Reparación'),
#             ('inspeccion', 'Inspección'),
#         ],
#         default='general'
#     )
#     
#     # Prioridad
#     prioridad = models.CharField(
#         max_length=20,
#         choices=[
#             ('baja', 'Baja'),
#             ('media', 'Media'),
#             ('alta', 'Alta'),
#             ('urgente', 'Urgente'),
#         ],
#         default='media'
#     )
#     
#     # Estado de la observación
#     estado = models.CharField(
#         max_length=20,
#         choices=[
#             ('abierta', 'Abierta'),
#             ('en_proceso', 'En Proceso'),
#             ('cerrada', 'Cerrada'),
#             ('cancelada', 'Cancelada'),
#         ],
#         default='abierta'
#     )
#     
#     # Timestamps y auditoría
#     fecha_creacion = models.DateTimeField(auto_now_add=True)
#     fecha_actualizacion = models.DateTimeField(auto_now=True)
#     fecha_vencimiento = models.DateTimeField(null=True, blank=True)
#     
#     # Usuario que creó la observación
#     usuario_creacion = models.ForeignKey(
#         'auth.User', 
#         on_delete=models.SET_NULL, 
#         null=True,
#         related_name='observaciones_creadas'
#     )
#     
#     # Usuario asignado (opcional)
#     usuario_asignado = models.ForeignKey(
#         'auth.User', 
#         on_delete=models.SET_NULL, 
#         null=True,
#         blank=True,
#         related_name='observaciones_asignadas'
#     )
#     
#     class Meta:
#         db_table = 'moviles_observaciones'
#         verbose_name = 'Observación de Móvil'
#         verbose_name_plural = 'Observaciones de Móviles'
#         ordering = ['-fecha_creacion']
#         indexes = [
#             models.Index(fields=['movil', 'fecha_creacion']),
#             models.Index(fields=['categoria']),
#             models.Index(fields=['estado']),
#             models.Index(fields=['prioridad']),
#         ]
#     
#     def __str__(self):
#         return f"{self.movil} - {self.titulo}"


# class MovilFoto(models.Model):  # MOVIDO A moviles/models.py
#     """
#     Fotos de cada móvil
#     Relación 1:N con moviles
#     """
#     
#     # Relación con móvil
#     movil = models.ForeignKey(
#         Movil, 
#         on_delete=models.CASCADE, 
#         related_name='fotos'
#     )
#     
#     # Archivo de imagen
#     imagen = models.ImageField(
#         upload_to='moviles/fotos/%Y/%m/',
#         help_text="Imagen del móvil"
#     )
#     
#     # Metadatos de la imagen
#     titulo = models.CharField(max_length=200, blank=True)
#     descripcion = models.TextField(blank=True)
#     
#     # Categorización
#     categoria = models.CharField(
#         max_length=50,
#         choices=[
#             ('exterior', 'Exterior'),
#             ('interior', 'Interior'),
#             ('documentos', 'Documentos'),
#             ('danos', 'Daños'),
#             ('mantenimiento', 'Mantenimiento'),
#             ('accesorios', 'Accesorios'),
#             ('general', 'General'),
#         ],
#         default='general'
#     )
#     
#     # Información técnica
#     tamaño_archivo = models.IntegerField(null=True, blank=True, help_text="Tamaño en bytes")
#     dimensiones = models.CharField(max_length=20, blank=True, help_text="Ancho x Alto en píxeles")
#     
#     # Geolocalización de la foto (opcional)
#     latitud = models.DecimalField(max_digits=10, decimal_places=6, null=True, blank=True)
#     longitud = models.DecimalField(max_digits=10, decimal_places=6, null=True, blank=True)
#     
#     # Orden y visibilidad
#     orden = models.IntegerField(default=0, help_text="Orden de visualización")
#     es_principal = models.BooleanField(default=False, help_text="Foto principal del móvil")
#     visible = models.BooleanField(default=True)
#     
#     # Timestamps y auditoría
#     fecha_captura = models.DateTimeField(auto_now_add=True)
#     fecha_actualizacion = models.DateTimeField(auto_now=True)
#     
#     # Usuario que subió la foto
#     usuario_captura = models.ForeignKey(
#         'auth.User', 
#         on_delete=models.SET_NULL, 
#         null=True,
#         related_name='fotos_capturadas'
#     )
#     
#     # Relación opcional con observación
#     observacion = models.ForeignKey(
#         MovilObservacion,
#         on_delete=models.SET_NULL,
#         null=True,
#         blank=True,
#         related_name='fotos'
#     )
#     
#     class Meta:
#         db_table = 'moviles_fotos'
#         verbose_name = 'Foto de Móvil'
#         verbose_name_plural = 'Fotos de Móviles'
#         ordering = ['orden', '-fecha_captura']
#         indexes = [
#             models.Index(fields=['movil', 'orden']),
#             models.Index(fields=['categoria']),
#             models.Index(fields=['es_principal']),
#             models.Index(fields=['fecha_captura']),
#         ]
#         constraints = [
#             # Solo una foto principal por móvil
#             models.UniqueConstraint(
#                 fields=['movil'],
#                 condition=models.Q(es_principal=True),
#                 name='unique_foto_principal_por_movil'
#             ),
#         ]
#     
#     def __str__(self):
#         return f"{self.movil} - {self.titulo or 'Foto'}"


# class MovilNota(models.Model):  # MOVIDO A moviles/models.py
#     """
#     Notas generales de cada móvil (campo de texto libre)
#     Relación 1:1 con moviles
#     """
#     
#     # Relación con móvil
#     movil = models.OneToOneField(
#         Movil, 
#         on_delete=models.CASCADE, 
#         related_name='nota_general',
#         primary_key=True
#     )
#     
#     # Contenido de la nota
#     contenido = models.TextField(
#         blank=True,
#         help_text="Notas generales sobre el móvil"
#     )
#     
#     # Timestamps
#     fecha_creacion = models.DateTimeField(auto_now_add=True)
#     fecha_actualizacion = models.DateTimeField(auto_now=True)
#     
#     # Usuario que actualizó la nota
#     usuario_actualizacion = models.ForeignKey(
#         'auth.User', 
#         on_delete=models.SET_NULL, 
#         null=True
#     )
#     
#     class Meta:
#         db_table = 'moviles_notas'
#         verbose_name = 'Nota de Móvil'
#         verbose_name_plural = 'Notas de Móviles'
#     
#     def __str__(self):
#         return f"Nota de {self.movil}"


class Posicion(models.Model):
    """Tabla de posiciones GPS históricas (POSICIONES)"""
    
    # Relaciones (normalización)
    empresa = models.ForeignKey('authentication.Empresa', on_delete=models.CASCADE, db_column='empresa_id')
    device_id = models.BigIntegerField()  # FK a dispositivos(id)
    movil = models.ForeignKey('moviles.Movil', on_delete=models.SET_NULL, null=True, blank=True, db_column='movil_id')
    evt_tipo_id = models.SmallIntegerField(null=True, blank=True)  # FK a evt_tipo(id)
    
    # Fechas y eventos
    fec_gps = models.DateTimeField(null=True, blank=True)
    fec_report = models.DateTimeField(null=True, blank=True)
    evento = models.CharField(max_length=10, blank=True, null=True)
    
    # Datos GPS
    velocidad = models.SmallIntegerField(null=True, blank=True)  # km/h
    rumbo = models.SmallIntegerField(null=True, blank=True)  # grados 0-359
    lat = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    lon = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    altitud = models.IntegerField(null=True, blank=True)
    
    # Calidad/señal
    sats = models.SmallIntegerField(null=True, blank=True)  # satélites
    hdop = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)  # precisión horizontal
    accuracy_m = models.IntegerField(null=True, blank=True)  # precisión en metros
    
    # Estado del vehículo
    ign_on = models.BooleanField(default=False)  # encendido/apagado
    batt_mv = models.IntegerField(null=True, blank=True)  # batería en mV
    ext_pwr_mv = models.IntegerField(null=True, blank=True)  # alimentación externa
    inputs_mask = models.CharField(max_length=20, blank=True, null=True)  # bits de entradas digitales
    outputs_mask = models.CharField(max_length=20, blank=True, null=True)  # bits de salidas digitales
    
    # Identificadores del mensaje para deduplicar
    msg_uid = models.CharField(max_length=64, blank=True, null=True)  # id único del mensaje
    seq = models.IntegerField(null=True, blank=True)  # secuencia del dispositivo
    
    # Proveedor/protocolo
    provider = models.CharField(max_length=32, blank=True, null=True)  # ej. "teltonika", "queclink"
    protocol = models.CharField(max_length=32, blank=True, null=True)
    
    # Crudo para trazabilidad
    raw_payload = models.TextField(blank=True, null=True)
    
    # Flags de calidad
    is_valid = models.BooleanField(default=True)  # después de filtros de limpieza
    is_late = models.BooleanField(default=False)  # arribó fuera de orden
    is_duplicate = models.BooleanField(default=False)
    
    # Dirección geocodificada
    direccion = models.TextField(blank=True, null=True, help_text="Dirección geocodificada de la posición")
    
    # Auditoría
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'posiciones'
        verbose_name = 'Posición GPS'
        verbose_name_plural = 'Posiciones GPS'
        indexes = [
            models.Index(fields=['movil', 'fec_gps']),
            models.Index(fields=['device_id', 'fec_gps']),
            models.Index(fields=['empresa', 'fec_gps']),
            models.Index(fields=['fec_gps']),
            models.Index(fields=['velocidad']),
            models.Index(fields=['ign_on']),
        ]
    
    def __str__(self):
        return f"Posición {self.movil.patente if self.movil else 'Device ' + str(self.device_id)} - {self.fec_gps}"
    
    @property
    def velocidad_kmh(self):
        """Retorna la velocidad en km/h"""
        return self.velocidad if self.velocidad is not None else 0
    
    @property
    def coordenadas(self):
        """Retorna las coordenadas como tupla (lat, lon)"""
        if self.lat is not None and self.lon is not None:
            return (float(self.lat), float(self.lon))
        return None
    
    @property
    def esta_detenido(self):
        """Determina si el vehículo estaba detenido (velocidad <= 5 km/h)"""
        return self.velocidad is not None and self.velocidad <= 5
    
    @property
    def calidad_senal(self):
        """Determina la calidad de la señal basada en satélites y HDOP"""
        if self.sats is None:
            return 'desconocida'
        
        if self.sats >= 8:
            return 'excelente'
        elif self.sats >= 6:
            return 'buena'
        elif self.sats >= 4:
            return 'regular'
        else:
            return 'mala'


# Create your models here.
