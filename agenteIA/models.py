from django.db import models
from django.contrib.auth.models import User


class VectorConsulta(models.Model):
    """
    Modelo para almacenar consultas pre-vectorizadas y sus acciones asociadas
    """
    CATEGORIA_CHOICES = [
        ('saludo', 'Saludo'),
        ('pasado', 'Consultas Pasadas'),
        ('actual', 'Estado Actual'),
        ('futuro', 'Consultas Futuras'),
        ('comando', 'Comandos'),
        ('cercania', 'Consultas de Cercanía'),
        ('ayuda', 'Ayuda y Soporte'),  # Nueva categoría
    ]
    
    TIPO_CONSULTA_CHOICES = [
        ('POSICION', 'Posición del Móvil'),
        ('RECORRIDO', 'Recorrido Histórico'),
        ('ESTADO', 'Estado del Móvil'),
        ('COMANDO_WHATSAPP', 'Comando: Enviar por WhatsApp'),
        ('LLEGADA', 'Estimación de Llegada'),
        ('SALUDO', 'Saludo'),
        ('CERCANIA', 'Cercanía a un Punto'),
        # Nuevos tipos
        ('LISTADO_ACTIVOS', 'Listado de Móviles Activos'),
        ('SITUACION_FLOTA', 'Situación de Flota'),
        ('MOVILES_EN_ZONA', 'Móviles en Zona'),
        ('AYUDA_GENERAL', 'Ayuda General'),
        ('VER_MAPA', 'Ver en Mapa/Google Maps'),
    ]
    
    # Texto original de la consulta
    texto_original = models.TextField(
        help_text="Texto de ejemplo de la consulta del usuario"
    )
    
    # Categoría de la consulta
    categoria = models.CharField(
        max_length=20,
        choices=CATEGORIA_CHOICES,
        help_text="Categoría de la consulta"
    )
    
    # Tipo de consulta específica
    tipo_consulta = models.CharField(
        max_length=50,
        choices=TIPO_CONSULTA_CHOICES,
        help_text="Tipo específico de consulta"
    )
    
    # Vector embedding (JSON)
    vector_embedding = models.JSONField(
        default=list,
        help_text="Vector embedding de la consulta"
    )
    
    # Acción a ejecutar cuando coincida
    accion_asociada = models.TextField(
        help_text="Descripción de qué acción realizar cuando la consulta coincida"
    )
    
    # Umbral de similitud
    threshold = models.FloatField(
        default=0.885,
        help_text="Umbral mínimo de similitud para considerar la consulta (0-1)"
    )
    
    # Variables para extracción (usando regex)
    variables = models.JSONField(
        default=dict,
        blank=True,
        help_text="Variables a extraer del texto (ej: {'movil': r'\\b[A-Z0-9]{3,10}\\b'})"
    )
    
    # Respuesta sugerida
    respuesta_template = models.TextField(
        blank=True,
        help_text="Plantilla de respuesta para esta consulta"
    )
    
    # Metadatos
    activo = models.BooleanField(
        default=True,
        help_text="Si está activo para usar en las consultas"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Vector de Consulta"
        verbose_name_plural = "Vectores de Consulta"
        ordering = ['categoria', 'tipo_consulta']
    
    def __str__(self):
        return f"{self.categoria} - {self.tipo_consulta}: {self.texto_original[:50]}..."


class ConversacionSofia(models.Model):
    """
    Modelo para almacenar las conversaciones con Sofia
    """
    usuario = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='conversaciones_sofia',
        null=True,
        blank=True
    )
    
    # Mensaje del usuario
    mensaje_usuario = models.TextField()
    
    # Respuesta de Sofia
    respuesta_sofia = models.TextField()
    
    # Vector utilizado para la consulta
    vector_usado = models.ForeignKey(
        VectorConsulta,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='conversaciones'
    )
    
    # Similitud encontrada
    similitud = models.FloatField(
        null=True,
        blank=True,
        help_text="Nivel de similitud con el vector de consulta"
    )
    
    # Datos adicionales de la consulta
    datos_consulta = models.JSONField(
        default=dict,
        blank=True,
        help_text="Datos extraídos de la consulta (móvil, fecha, etc)"
    )
    
    # Estado de la consulta
    procesado = models.BooleanField(
        default=True,
        help_text="Si la consulta fue procesada exitosamente"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Conversación con Sofia"
        verbose_name_plural = "Conversaciones con Sofia"
        ordering = ['-created_at']
    
    def __str__(self):
        usuario_str = self.usuario.username if self.usuario else "Anónimo"
        return f"{usuario_str} - {self.mensaje_usuario[:50]}..."


class ZonaInteres(models.Model):
    """
    Modelo para almacenar zonas de interés para cálculos de llegada
    """
    usuario = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='zonas_interes'
    )
    
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)
    
    # Coordenadas (usando GeoDjango)
    latitud = models.FloatField()
    longitud = models.FloatField()
    
    # Radio en metros
    radio_metros = models.IntegerField(default=100, help_text="Radio de la zona en metros")
    
    activo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Zona de Interés"
        verbose_name_plural = "Zonas de Interés"
        ordering = ['nombre']
    
    def __str__(self):
        return f"{self.nombre} ({self.latitud}, {self.longitud})"

