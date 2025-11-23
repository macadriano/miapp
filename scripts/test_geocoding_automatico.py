#!/usr/bin/env python
"""
Script para probar la geocodificación automática
"""

import os
import sys
import django
from django.utils import timezone

# Configurar Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wayproject.settings')
django.setup()

from gps.models import Movil, MovilStatus

def test_geocodificacion_automatica():
    """
    Probar la geocodificación automática actualizando coordenadas
    """
    
    print("=" * 80)
    print("TESTING DE GEOCODIFICACION AUTOMATICA")
    print("=" * 80)
    
    try:
        # Buscar un móvil sin geocodificación
        movil = Movil.objects.filter(
            geocode__isnull=True
        ).first()
        
        if not movil:
            print("No hay móviles sin geocodificación para probar")
            return
        
        print(f"1. Móvil seleccionado: {movil.patente} ({movil.alias})")
        
        # Obtener el status del móvil
        status = movil.status
        
        print(f"2. Status actual: {status.ultimo_lat}, {status.ultimo_lon}")
        
        # Simular nueva coordenada (un poco diferente para que se detecte como cambio)
        if status.ultimo_lat and status.ultimo_lon:
            nueva_lat = float(status.ultimo_lat) + 0.0001
            nueva_lon = float(status.ultimo_lon) + 0.0001
            
            print(f"3. Actualizando coordenadas a: {nueva_lat}, {nueva_lon}")
            
            # Actualizar coordenadas (esto debería disparar la señal automática)
            status.ultimo_lat = nueva_lat
            status.ultimo_lon = nueva_lon
            status.ultima_actualizacion = timezone.now()
            status.save()
            
            print("4. Coordenadas actualizadas - señal automática disparada")
            
            # Esperar un momento para que se procese
            import time
            time.sleep(2)
            
            # Verificar si se creó la geocodificación
            try:
                geocode = movil.geocode
                if geocode.direccion_formateada:
                    print("5. Geocodificación automática exitosa:")
                    print(f"   - Dirección: {geocode.direccion_formateada}")
                    print(f"   - Localidad: {geocode.localidad}")
                    print(f"   - Provincia: {geocode.provincia}")
                    print(f"   - Fuente: {geocode.fuente_geocodificacion}")
                else:
                    print("5. Geocodificación automática falló - sin dirección")
            except Exception as e:
                print(f"5. Error verificando geocodificación: {e}")
        else:
            print("3. El móvil no tiene coordenadas para probar")
            
    except Exception as e:
        print(f"Error en testing: {e}")
        import traceback
        traceback.print_exc()

def test_creacion_posicion_historica():
    """
    Probar la creación automática de posición histórica
    """
    
    print("\n" + "=" * 80)
    print("TESTING DE CREACION AUTOMATICA DE POSICION HISTORICA")
    print("=" * 80)
    
    try:
        from gps.models import Posicion
        
        # Buscar un móvil con coordenadas
        movil = Movil.objects.filter(
            status__ultimo_lat__isnull=False,
            status__ultimo_lon__isnull=False
        ).first()
        
        if not movil:
            print("No hay móviles con coordenadas para probar")
            return
        
        print(f"1. Móvil seleccionado: {movil.patente}")
        
        # Contar posiciones históricas antes
        posiciones_antes = Posicion.objects.filter(movil=movil).count()
        print(f"2. Posiciones históricas antes: {posiciones_antes}")
        
        # Actualizar coordenadas ligeramente
        status = movil.status
        if status.ultimo_lat and status.ultimo_lon:
            nueva_lat = float(status.ultimo_lat) + 0.0001
            nueva_lon = float(status.ultimo_lon) + 0.0001
            
            print(f"3. Actualizando coordenadas a: {nueva_lat}, {nueva_lon}")
            
            status.ultimo_lat = nueva_lat
            status.ultimo_lon = nueva_lon
            status.fecha_gps = timezone.now()
            status.save()
            
            print("4. Coordenadas actualizadas - señal automática disparada")
            
            # Esperar un momento
            import time
            time.sleep(2)
            
            # Contar posiciones históricas después
            posiciones_despues = Posicion.objects.filter(movil=movil).count()
            print(f"5. Posiciones históricas después: {posiciones_despues}")
            
            if posiciones_despues > posiciones_antes:
                print("6. Creación automática de posición histórica exitosa")
            else:
                print("6. No se creó nueva posición histórica")
                
    except Exception as e:
        print(f"Error en testing de posiciones: {e}")

if __name__ == "__main__":
    test_geocodificacion_automatica()
    test_creacion_posicion_historica()
    
    print("\n" + "=" * 80)
    print("TESTING COMPLETADO")
    print("=" * 80)
