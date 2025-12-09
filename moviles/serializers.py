from rest_framework import serializers
from .models import Movil, MovilStatus, MovilGeocode, MovilObservacion, MovilFoto, MovilNota


class MovilSerializer(serializers.ModelSerializer):
    """Serializer para el modelo Movil"""
    
    # Campos calculados
    equipo_gps_info = serializers.SerializerMethodField()
    status_info = serializers.SerializerMethodField()
    geocode_info = serializers.SerializerMethodField()
    nota_general = serializers.SerializerMethodField()
    fotos_count = serializers.SerializerMethodField()
    observaciones_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Movil
        fields = '__all__'
    
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
        """Retorna información del estado del móvil utilizando datos precargados"""
        status = getattr(obj, 'status', None)
        if not status:
            return None

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
    
    def get_geocode_info(self, obj):
        """Retorna información de geocodificación del móvil utilizando datos precargados"""
        geocode = getattr(obj, 'geocode', None)
        if not geocode:
            return None

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
    
    def get_nota_general(self, obj):
        """Retorna la nota general del móvil utilizando datos precargados"""
        nota = getattr(obj, 'nota_general', None)
        if not nota:
            return None

        return {
            'contenido': nota.contenido,
            'fecha_actualizacion': nota.fecha_actualizacion,
            'usuario_actualizacion': nota.usuario_actualizacion.username if nota.usuario_actualizacion else None
        }
    
    def get_fotos_count(self, obj):
        """Retorna el número de fotos del móvil utilizando anotaciones"""
        return getattr(obj, 'fotos_total', None) or 0
    
    def get_observaciones_count(self, obj):
        """Retorna el número de observaciones del móvil utilizando anotaciones"""
        return getattr(obj, 'observaciones_total', None) or 0


class MovilStatusSerializer(serializers.ModelSerializer):
    """Serializer para el modelo MovilStatus"""
    
    class Meta:
        model = MovilStatus
        fields = '__all__'


class MovilGeocodeSerializer(serializers.ModelSerializer):
    """Serializer para el modelo MovilGeocode"""
    
    class Meta:
        model = MovilGeocode
        fields = '__all__'


class MovilObservacionSerializer(serializers.ModelSerializer):
    """Serializer para el modelo MovilObservacion"""
    
    class Meta:
        model = MovilObservacion
        fields = '__all__'


class MovilFotoSerializer(serializers.ModelSerializer):
    """Serializer para el modelo MovilFoto"""
    
    class Meta:
        model = MovilFoto
        fields = '__all__'


class MovilNotaSerializer(serializers.ModelSerializer):
    """Serializer para el modelo MovilNota"""
    
    class Meta:
        model = MovilNota
        fields = '__all__'
