"""
Señales Django para geocodificación automática
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction
from moviles.models import MovilStatus, MovilGeocode
from .services import geocoding_service

@receiver(post_save, sender=MovilStatus)
def actualizar_geocodificacion_automatica(sender, instance, created, **kwargs):
    """
    Señal que se ejecuta automáticamente cuando se actualiza MovilStatus
    Si las coordenadas han cambiado, geocodifica automáticamente
    """
    
    # Solo procesar si no es una creación inicial o si las coordenadas están presentes
    if created and (not instance.ultimo_lat or not instance.ultimo_lon):
        return
    
    # Verificar si las coordenadas están presentes
    if not instance.ultimo_lat or not instance.ultimo_lon:
        return
    
    try:
        # Obtener el móvil asociado
        movil = instance.movil
        
        # Verificar si ya tiene geocodificación reciente (últimas 24 horas)
        from django.utils import timezone
        from datetime import timedelta
        
        try:
            geocode = movil.geocode
            if geocode.fecha_geocodificacion:
                # Si la geocodificación es reciente, no volver a geocodificar
                tiempo_diferencia = timezone.now() - geocode.fecha_geocodificacion
                if tiempo_diferencia < timedelta(hours=24):
                    print(f"Geocodificación reciente para móvil {movil.patente}, omitiendo")
                    return
        except MovilGeocode.DoesNotExist:
            pass  # No hay geocodificación, proceder
        
        # Ejecutar geocodificación en una transacción separada para evitar bloqueos
        def geocodificar_async():
            try:
                print(f"Geocodificación automática para móvil {movil.patente}")
                geocoding_service.actualizar_geocodificacion_movil(movil.id)
            except Exception as e:
                print(f"Error en geocodificación automática para móvil {movil.patente}: {e}")
        
        # Ejecutar en transacción separada
        with transaction.atomic():
            geocodificar_async()
            
    except Exception as e:
        print(f"Error en señal de geocodificación automática: {e}")

@receiver(post_save, sender=MovilStatus)
def crear_posicion_historica(sender, instance, created, **kwargs):
    """
    Señal que crea automáticamente una posición histórica cuando se actualiza MovilStatus
    """
    
    # Solo procesar si las coordenadas están presentes
    if not instance.ultimo_lat or not instance.ultimo_lon:
        return
    
    try:
        from .models import Posicion
        
        # Verificar si ya existe una posición reciente para evitar duplicados
        from django.utils import timezone
        from datetime import timedelta
        
        posicion_reciente = Posicion.objects.filter(
            movil=instance.movil,
            lat=instance.ultimo_lat,
            lon=instance.ultimo_lon,
            fec_gps__gte=timezone.now() - timedelta(minutes=5)
        ).first()
        
        if posicion_reciente:
            print(f"Posición reciente ya existe para móvil {instance.movil.patente}")
            return
        
        # Crear nueva posición histórica
        posicion = Posicion.objects.create(
            empresa_id=1,  # ID de empresa por defecto
            movil=instance.movil,
            device_id=str(instance.movil.gps_id) if instance.movil.gps_id else None,
            lat=instance.ultimo_lat,
            lon=instance.ultimo_lon,
            altitud=instance.ultima_altitud,
            velocidad=int(instance.ultima_velocidad_kmh) if instance.ultima_velocidad_kmh else 0,
            rumbo=int(instance.ultimo_rumbo) if instance.ultimo_rumbo else 0,
            sats=instance.satelites,
            hdop=instance.hdop,
            ign_on=instance.ignicion,
            fec_gps=instance.fecha_gps or timezone.now(),
            fec_report=timezone.now(),
            raw_payload=instance.raw_data,
            is_valid=True
        )
        
        # Actualizar referencia en status
        instance.id_ultima_posicion = posicion.id
        instance.save(update_fields=['id_ultima_posicion'])
        
        print(f"Posición histórica creada para móvil {instance.movil.patente}: ID {posicion.id}")
        
    except Exception as e:
        print(f"Error creando posición histórica para móvil {instance.movil.patente}: {e}")
