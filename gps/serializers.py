from rest_framework import serializers
from .models import Equipo, Posicion, CatMovil, TipoEquipoGPS, ConfiguracionReceptor, EstadisticasRecepcion
from moviles.models import Movil, MovilStatus, MovilGeocode, MovilObservacion, MovilFoto, MovilNota


class MovilSerializer(serializers.ModelSerializer):
    equipo_gps_info = serializers.SerializerMethodField(read_only=True)
    status_info = serializers.SerializerMethodField(read_only=True)
    geocode_info = serializers.SerializerMethodField(read_only=True)
    nota_general = serializers.SerializerMethodField(read_only=True)
    fotos_count = serializers.SerializerMethodField(read_only=True)
    observaciones_count = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = Movil
        fields = [
            'id', 'codigo', 'alias', 'patente', 'vin',
            'marca', 'modelo', 'anio', 'color', 'tipo_vehiculo',
            'gps_id', 'activo', 'created_at', 'updated_at',
            'equipo_gps_info', 'status_info', 'geocode_info',
            'nota_general', 'fotos_count', 'observaciones_count'
        ]
        read_only_fields = ('id', 'created_at', 'updated_at', 'equipo_gps_info', 'status_info', 'geocode_info', 'nota_general', 'fotos_count', 'observaciones_count')
    
    def get_equipo_gps_info(self, obj):
        """Retorna información del equipo GPS asignado (por gps_id/IMEI)"""
        try:
            equipo = obj.get_equipo_gps()
            if equipo:
                return {
                    'id': equipo.id,
                    'imei': equipo.imei,
                    'marca': equipo.marca,
                    'modelo': equipo.modelo,
                    'numero_serie': equipo.numero_serie,
                    'estado': equipo.estado,
                    'fecha_instalacion': equipo.fecha_instalacion,
                    'empresa_id': equipo.empresa_id if hasattr(equipo, 'empresa_id') else None
                }
        except Exception:
            pass
        return None
    
    def get_status_info(self, obj):
        """Retorna información del estado del móvil"""
        try:
            # Usar consulta directa en lugar de obj.status
            status = MovilStatus.objects.filter(movil=obj).first()
            if status:
                # Convertir fecha_gps a zona horaria de Argentina
                fecha_gps_argentina = None
                if status.fecha_gps:
                    try:
                        from zoneinfo import ZoneInfo
                        tz_argentina = ZoneInfo('America/Argentina/Buenos_Aires')
                    except ImportError:
                        from datetime import timezone, timedelta
                        tz_argentina = timezone(timedelta(hours=-3))
                    
                    if status.fecha_gps.tzinfo:
                        fecha_gps_argentina = status.fecha_gps.astimezone(tz_argentina)
                    else:
                        fecha_gps_argentina = status.fecha_gps.replace(tzinfo=tz_argentina)
                    fecha_gps_argentina = fecha_gps_argentina.isoformat()
                
                return {
                    'ultimo_lat': status.ultimo_lat,
                    'ultimo_lon': status.ultimo_lon,
                    'ultima_altitud': status.ultima_altitud,
                    'ultima_velocidad_kmh': status.ultima_velocidad_kmh,
                    'ultimo_rumbo': status.ultimo_rumbo,
                    'satelites': status.satelites,
                    'hdop': status.hdop,
                    'calidad_senal': status.calidad_senal,
                    'ignicion': status.ignicion,
                    'bateria_pct': status.bateria_pct,
                    'odometro_km': status.odometro_km,
                    'estado_conexion': status.estado_conexion,
                    'fecha_gps': fecha_gps_argentina,
                    'fecha_recepcion': status.fecha_recepcion,
                    'ultima_actualizacion': status.ultima_actualizacion
                }
        except Exception:
            pass
        return None
    
    def get_geocode_info(self, obj):
        """Retorna información de geocodificación del móvil"""
        try:
            # Usar consulta directa en lugar de obj.geocode
            geocode = MovilGeocode.objects.filter(movil=obj).first()
            if geocode:
                return {
                    'direccion_formateada': geocode.direccion_formateada,
                    'calle': geocode.calle,
                    'numero': geocode.numero,
                    'piso': geocode.piso,
                    'depto': geocode.depto,
                    'barrio': geocode.barrio,
                    'localidad': geocode.localidad,
                    'municipio': geocode.municipio,
                    'provincia': geocode.provincia,
                    'codigo_postal': geocode.codigo_postal,
                    'pais': geocode.pais,
                    'fuente_geocodificacion': geocode.fuente_geocodificacion,
                    'confianza_geocodificacion': geocode.confianza_geocodificacion,
                    'geohash': geocode.geohash,
                    'fecha_geocodificacion': geocode.fecha_geocodificacion
                }
        except Exception:
            pass
        return None
    
    def get_nota_general(self, obj):
        """Retorna la nota general del móvil"""
        try:
            # Usar consulta directa en lugar de obj.nota_general
            nota = MovilNota.objects.filter(movil=obj, es_general=True).first()
            if nota:
                return {
                    'contenido': nota.contenido,
                    'fecha_actualizacion': nota.fecha_actualizacion,
                    'usuario_actualizacion': nota.usuario_actualizacion.username if nota.usuario_actualizacion else None
                }
        except Exception:
            pass
        return None
    
    def get_fotos_count(self, obj):
        """Retorna el número de fotos del móvil"""
        try:
            return MovilFoto.objects.filter(movil=obj).count()
        except Exception:
            return 0
    
    def get_observaciones_count(self, obj):
        """Retorna el número de observaciones del móvil"""
        try:
            return MovilObservacion.objects.filter(movil=obj).count()
        except Exception:
            return 0
    
    def validate_patente(self, value):
        """Validar que la patente no esté duplicada (excepto al editar)"""
        if value:
            # Obtener el ID del móvil que se está editando (si existe)
            movil_id = self.instance.id if self.instance else None
            
            # Verificar si ya existe otra patente igual
            qs = Movil.objects.filter(patente=value)
            if movil_id:
                qs = qs.exclude(id=movil_id)
            
            if qs.exists():
                raise serializers.ValidationError('Ya existe un móvil con esta patente')
        
        return value
    
    def validate_gps_id(self, value):
        """Validar que el GPS ID no esté duplicado (excepto al editar)"""
        if value:
            movil_id = self.instance.id if self.instance else None
            qs = Movil.objects.filter(gps_id=value)
            if movil_id:
                qs = qs.exclude(id=movil_id)
            
            if qs.exists():
                raise serializers.ValidationError('Ya existe un móvil con este GPS ID')
        
        return value
    
    def validate_codigo(self, value):
        """Validar que el código no esté duplicado (excepto al editar)"""
        if value:
            movil_id = self.instance.id if self.instance else None
            qs = Movil.objects.filter(codigo=value)
            if movil_id:
                qs = qs.exclude(id=movil_id)
            
            if qs.exists():
                raise serializers.ValidationError('Ya existe un móvil con este código')
        
        return value


class EquipoSerializer(serializers.ModelSerializer):
    movil_info = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = Equipo
        fields = [
            'id', 'imei', 'numero_serie', 'marca', 'modelo', 
            'estado', 'empresa', 'fecha_instalacion',
            'created_at', 'updated_at', 'movil_info'
        ]
        read_only_fields = ('id', 'created_at', 'updated_at', 'empresa', 'movil_info')
    
    def get_movil_info(self, obj):
        """Retorna información del móvil asignado (si existe)"""
        try:
            movil = obj.get_movil_asignado()
            if movil:
                return {
                    'id': movil.id,
                    'patente': movil.patente,
                    'alias': movil.alias,
                    'codigo': movil.codigo,
                    'marca': movil.marca,
                    'modelo': movil.modelo,
                    'activo': movil.activo
                }
            return None
        except Exception:
            return None
    
    def create(self, validated_data):
        """Crear equipo estableciendo created_at y updated_at manualmente"""
        from django.utils import timezone
        validated_data['created_at'] = timezone.now()
        validated_data['updated_at'] = timezone.now()
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        """Actualizar equipo estableciendo updated_at manualmente"""
        from django.utils import timezone
        validated_data['updated_at'] = timezone.now()
        return super().update(instance, validated_data)
    
    def validate_imei(self, value):
        """Validar que el IMEI no esté duplicado"""
        if value:
            equipo_id = self.instance.id if self.instance else None
            qs = Equipo.objects.filter(imei=value)
            if equipo_id:
                qs = qs.exclude(id=equipo_id)
            
            if qs.exists():
                raise serializers.ValidationError('Ya existe un equipo con este IMEI')
        
        return value
    
    def validate_numero_serie(self, value):
        """Validar que el número de serie no esté duplicado si se proporciona"""
        if value:
            equipo_id = self.instance.id if self.instance else None
            qs = Equipo.objects.filter(numero_serie=value)
            if equipo_id:
                qs = qs.exclude(id=equipo_id)
            
            if qs.exists():
                raise serializers.ValidationError('Ya existe un equipo con este número de serie')
        
        return value


# Serializers para los nuevos modelos
class MovilStatusSerializer(serializers.ModelSerializer):
    fecha_gps = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = MovilStatus
        fields = '__all__'
        read_only_fields = ('movil', 'ultima_actualizacion')
    
    def get_fecha_gps(self, obj):
        """Devolver fecha_gps en zona horaria de Argentina (UTC-3)"""
        if not obj.fecha_gps:
            return None
        
        try:
            from zoneinfo import ZoneInfo
            tz_argentina = ZoneInfo('America/Argentina/Buenos_Aires')
        except ImportError:
            from datetime import timezone, timedelta
            tz_argentina = timezone(timedelta(hours=-3))
        
        # Convertir a zona horaria de Argentina si tiene timezone
        if obj.fecha_gps.tzinfo:
            fecha_argentina = obj.fecha_gps.astimezone(tz_argentina)
        else:
            # Si no tiene timezone, asumir que ya está en hora local de Argentina
            fecha_argentina = obj.fecha_gps.replace(tzinfo=tz_argentina)
        
        return fecha_argentina.isoformat()


class MovilGeocodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = MovilGeocode
        fields = '__all__'
        read_only_fields = ('movil', 'fecha_actualizacion')


class PosicionSerializer(serializers.ModelSerializer):
    """Serializer para posiciones GPS históricas"""
    movil_info = serializers.SerializerMethodField(read_only=True)
    velocidad_kmh = serializers.ReadOnlyField()
    coordenadas = serializers.ReadOnlyField()
    esta_detenido = serializers.ReadOnlyField()
    calidad_senal = serializers.ReadOnlyField()
    fec_gps = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = Posicion
        fields = [
            'id', 'empresa', 'device_id', 'movil', 'evt_tipo_id',
            'fec_gps', 'fec_report', 'evento', 'velocidad', 'rumbo',
            'lat', 'lon', 'altitud', 'sats', 'hdop', 'accuracy_m',
            'ign_on', 'batt_mv', 'ext_pwr_mv', 'inputs_mask', 'outputs_mask',
            'msg_uid', 'seq', 'provider', 'protocol', 'raw_payload',
            'is_valid', 'is_late', 'is_duplicate', 'direccion', 'created_at',
            'movil_info', 'velocidad_kmh', 'coordenadas', 'esta_detenido', 'calidad_senal'
        ]
        read_only_fields = ('created_at',)
    
    def get_movil_info(self, obj):
        """Información del móvil asociado"""
        if obj.movil:
            return {
                'id': obj.movil.id,
                'patente': obj.movil.patente,
                'alias': obj.movil.alias,
                'codigo': obj.movil.codigo,
                'marca': obj.movil.marca,
                'modelo': obj.movil.modelo
            }
        return None
    
    def get_fec_gps(self, obj):
        """Devolver fec_gps en zona horaria de Argentina (UTC-3)"""
        if not obj.fec_gps:
            return None
        
        try:
            from zoneinfo import ZoneInfo
            tz_argentina = ZoneInfo('America/Argentina/Buenos_Aires')
        except ImportError:
            from datetime import timezone, timedelta
            tz_argentina = timezone(timedelta(hours=-3))
        
        # Convertir a zona horaria de Argentina si tiene timezone
        if obj.fec_gps.tzinfo:
            fecha_argentina = obj.fec_gps.astimezone(tz_argentina)
        else:
            # Si no tiene timezone, asumir que ya está en hora local de Argentina
            fecha_argentina = obj.fec_gps.replace(tzinfo=tz_argentina)
        
        return fecha_argentina.isoformat()


class PosicionRecorridoSerializer(serializers.ModelSerializer):
    """Serializer liviano para recorridos (solo campos necesarios para UI)."""

    timestamp = serializers.SerializerMethodField(read_only=True)
    satelites = serializers.SerializerMethodField(read_only=True)
    ignicion = serializers.BooleanField(source='ign_on', read_only=True)
    calidad = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Posicion
        fields = [
            'id',
            'movil',
            'fec_gps',
            'timestamp',
            'velocidad',
            'rumbo',
            'lat',
            'lon',
            'altitud',
            'sats',
            'satelites',
            'hdop',
            'ign_on',
            'ignicion',
            'direccion',
            'calidad',
        ]
        read_only_fields = fields

    def get_timestamp(self, obj):
        """Devolver timestamp en zona horaria de Argentina (UTC-3)"""
        if not obj.fec_gps:
            return None
        
        try:
            from zoneinfo import ZoneInfo
            tz_argentina = ZoneInfo('America/Argentina/Buenos_Aires')
        except ImportError:
            from datetime import timezone, timedelta
            tz_argentina = timezone(timedelta(hours=-3))
        
        # Convertir a zona horaria de Argentina si tiene timezone
        if obj.fec_gps.tzinfo:
            fecha_argentina = obj.fec_gps.astimezone(tz_argentina)
        else:
            # Si no tiene timezone, asumir que ya está en hora local de Argentina
            fecha_argentina = obj.fec_gps.replace(tzinfo=tz_argentina)
        
        return fecha_argentina.isoformat()

    def get_satelites(self, obj):
        return obj.sats

    def get_calidad(self, obj):
        return obj.calidad_senal


class RecorridoStatsSerializer(serializers.Serializer):
    """Serializer para estadísticas de un recorrido"""
    movil_id = serializers.IntegerField()
    movil_info = serializers.DictField()
    fecha_inicio = serializers.DateTimeField()
    fecha_fin = serializers.DateTimeField()
    duracion_minutos = serializers.IntegerField()
    distancia_km = serializers.FloatField()
    velocidad_maxima = serializers.IntegerField()
    velocidad_promedio = serializers.FloatField()
    puntos_gps = serializers.IntegerField()
    detenciones = serializers.IntegerField()
    tiempo_detenido_minutos = serializers.IntegerField()
    tiempo_movimiento_minutos = serializers.IntegerField()
    eficiencia_combustible = serializers.FloatField(allow_null=True)
    rango_velocidades = serializers.DictField()
    estadisticas_por_hora = serializers.ListField()


class RecorridoFiltrosSerializer(serializers.Serializer):
    """Serializer para filtros de recorridos"""
    movil_id = serializers.IntegerField(required=False)
    fecha_desde = serializers.DateTimeField(required=False)
    fecha_hasta = serializers.DateTimeField(required=False)
    velocidad_min = serializers.IntegerField(required=False)
    velocidad_max = serializers.IntegerField(required=False)
    solo_detenciones = serializers.BooleanField(default=False)
    solo_movimiento = serializers.BooleanField(default=False)
    ignicion_encendida = serializers.BooleanField(required=False)
    calidad_senal = serializers.ChoiceField(
        choices=['excelente', 'buena', 'regular', 'mala', 'desconocida'],
        required=False
    )
    limite_registros = serializers.IntegerField(default=10000, max_value=50000)


class CatMovilSerializer(serializers.ModelSerializer):
    class Meta:
        model = CatMovil
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')


class TipoEquipoGPSSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoEquipoGPS
        fields = '__all__'


class ConfiguracionReceptorSerializer(serializers.ModelSerializer):
    tipo_equipo_nombre = serializers.CharField(source='tipo_equipo.nombre', read_only=True)
    
    class Meta:
        model = ConfiguracionReceptor
        fields = '__all__'
        read_only_fields = ('tipo_equipo_nombre',)


class EstadisticasRecepcionSerializer(serializers.ModelSerializer):
    receptor_nombre = serializers.CharField(source='receptor.nombre', read_only=True)
    
    class Meta:
        model = EstadisticasRecepcion
        fields = '__all__'
        read_only_fields = ('receptor_nombre',)


# Serializers para los nuevos modelos de observaciones, fotos y notas
class MovilObservacionSerializer(serializers.ModelSerializer):
    usuario_creacion_nombre = serializers.CharField(source='usuario_creacion.username', read_only=True)
    usuario_asignado_nombre = serializers.CharField(source='usuario_asignado.username', read_only=True)
    fotos_count = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = MovilObservacion
        fields = [
            'id', 'movil', 'titulo', 'contenido', 'categoria', 'prioridad', 'estado',
            'fecha_creacion', 'fecha_actualizacion', 'fecha_vencimiento',
            'usuario_creacion', 'usuario_asignado', 'usuario_creacion_nombre', 
            'usuario_asignado_nombre', 'fotos_count'
        ]
        read_only_fields = ('id', 'fecha_creacion', 'fecha_actualizacion', 'usuario_creacion_nombre', 'usuario_asignado_nombre', 'fotos_count')
    
    def get_fotos_count(self, obj):
        """Retorna el número de fotos asociadas a esta observación"""
        return obj.fotos.count()
    
    def create(self, validated_data):
        """Crear observación asignando automáticamente el usuario actual"""
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['usuario_creacion'] = request.user
        return super().create(validated_data)


class MovilFotoSerializer(serializers.ModelSerializer):
    usuario_captura_nombre = serializers.CharField(source='usuario_captura.username', read_only=True)
    imagen_url = serializers.SerializerMethodField(read_only=True)
    imagen_thumbnail = serializers.SerializerMethodField(read_only=True)
    tamaño_formateado = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = MovilFoto
        fields = [
            'id', 'movil', 'imagen', 'imagen_url', 'imagen_thumbnail',
            'titulo', 'descripcion', 'categoria', 'tamaño_archivo', 'tamaño_formateado',
            'dimensiones', 'latitud', 'longitud', 'orden', 'es_principal', 'visible',
            'fecha_captura', 'fecha_actualizacion', 'usuario_captura', 
            'usuario_captura_nombre', 'observacion'
        ]
        read_only_fields = ('id', 'fecha_captura', 'fecha_actualizacion', 'usuario_captura_nombre', 'imagen_url', 'imagen_thumbnail', 'tamaño_formateado')
    
    def get_imagen_url(self, obj):
        """Retorna la URL completa de la imagen"""
        if obj.imagen:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.imagen.url)
            return obj.imagen.url
        return None
    
    def get_imagen_thumbnail(self, obj):
        """Retorna la URL del thumbnail de la imagen"""
        if obj.imagen:
            request = self.context.get('request')
            if request:
                # Aquí podrías implementar lógica para generar thumbnails
                return request.build_absolute_uri(obj.imagen.url)
            return obj.imagen.url
        return None
    
    def get_tamaño_formateado(self, obj):
        """Retorna el tamaño del archivo formateado"""
        if obj.tamaño_archivo:
            size = obj.tamaño_archivo
            if size < 1024:
                return f"{size} B"
            elif size < 1024 * 1024:
                return f"{size / 1024:.1f} KB"
            else:
                return f"{size / (1024 * 1024):.1f} MB"
        return None
    
    def create(self, validated_data):
        """Crear foto asignando automáticamente el usuario actual"""
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['usuario_captura'] = request.user
        
        # Calcular tamaño del archivo si no se proporciona
        if 'tamaño_archivo' not in validated_data and validated_data.get('imagen'):
            try:
                validated_data['tamaño_archivo'] = validated_data['imagen'].size
            except:
                pass
        
        return super().create(validated_data)


class MovilNotaSerializer(serializers.ModelSerializer):
    usuario_actualizacion_nombre = serializers.CharField(source='usuario_actualizacion.username', read_only=True)
    
    class Meta:
        model = MovilNota
        fields = [
            'movil', 'contenido', 'fecha_creacion', 'fecha_actualizacion',
            'usuario_actualizacion', 'usuario_actualizacion_nombre'
        ]
        read_only_fields = ('fecha_creacion', 'fecha_actualizacion', 'usuario_actualizacion_nombre')
    
    def update(self, instance, validated_data):
        """Actualizar nota asignando automáticamente el usuario actual"""
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['usuario_actualizacion'] = request.user
        return super().update(instance, validated_data)