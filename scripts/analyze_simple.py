#!/usr/bin/env python
"""
Script simple para analizar la estructura actual
"""

import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wayproject.settings')
django.setup()

from django.db import connection
from gps.models import Movil, Equipo

def analyze_current_structure():
    """Analizar estructura actual"""
    
    print("=" * 80)
    print("ANALISIS DE ESTRUCTURA ACTUAL - WAYGPS")
    print("=" * 80)
    
    # Contar registros
    print("\nREGISTROS ACTUALES:")
    print("-" * 50)
    print(f"  - Moviles: {Movil.objects.count()}")
    print(f"  - Equipos: {Equipo.objects.count()}")
    
    # Verificar datos de ejemplo
    if Movil.objects.exists():
        print("\nEJEMPLO DE MOVIL:")
        movil = Movil.objects.first()
        print(f"  - ID: {movil.id}")
        print(f"  - Patente: {movil.patente}")
        print(f"  - GPS ID: {movil.gps_id}")
        print(f"  - Ultima lat: {movil.ultimo_lat}")
        print(f"  - Ultima lon: {movil.ultimo_lon}")
        print(f"  - Velocidad: {movil.ultima_velocidad_kmh}")
    
    if Equipo.objects.exists():
        print("\nEJEMPLO DE EQUIPO:")
        equipo = Equipo.objects.first()
        print(f"  - ID: {equipo.id}")
        print(f"  - IMEI: {equipo.imei}")
        print(f"  - Marca: {equipo.marca}")
        print(f"  - Modelo: {equipo.modelo}")
        print(f"  - Estado: {equipo.estado}")
    
    # Analizar campos del modelo Movil
    print("\nCAMPOS DEL MODELO MOVIL:")
    print("-" * 50)
    movil_fields = Movil._meta.get_fields()
    for field in movil_fields:
        if hasattr(field, 'name'):
            field_type = type(field).__name__
            null_info = "NULL" if field.null else "NOT NULL"
            print(f"  - {field.name}: {field_type} ({null_info})")
    
    # Analizar campos del modelo Equipo
    print("\nCAMPOS DEL MODELO EQUIPO:")
    print("-" * 50)
    equipo_fields = Equipo._meta.get_fields()
    for field in equipo_fields:
        if hasattr(field, 'name'):
            field_type = type(field).__name__
            null_info = "NULL" if field.null else "NOT NULL"
            print(f"  - {field.name}: {field_type} ({null_info})")

if __name__ == "__main__":
    try:
        analyze_current_structure()
        print("\n" + "=" * 80)
        print("ANALISIS COMPLETADO")
        print("=" * 80)
        
    except Exception as e:
        print(f"Error en el analisis: {e}")
        import traceback
        traceback.print_exc()
