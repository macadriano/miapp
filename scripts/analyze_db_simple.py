#!/usr/bin/env python
"""
Script simple para analizar la estructura de la base de datos
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

def analyze_database():
    """Analizar estructura de la base de datos"""
    
    print("=" * 80)
    print("ANALISIS DE BASE DE DATOS - WAYGPS")
    print("=" * 80)
    
    with connection.cursor() as cursor:
        # Obtener todas las tablas
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_type = 'BASE TABLE'
            ORDER BY table_name;
        """)
        
        tables = cursor.fetchall()
        
        print(f"\nTABLAS EXISTENTES ({len(tables)}):")
        print("-" * 50)
        
        for table in tables:
            table_name = table[0]
            print(f"\nTABLA: {table_name}")
            print("-" * 30)
            
            # Obtener campos de la tabla
            cursor.execute(f"""
                SELECT 
                    column_name,
                    data_type,
                    is_nullable,
                    column_default
                FROM information_schema.columns 
                WHERE table_name = '{table_name}'
                ORDER BY ordinal_position;
            """)
            
            columns = cursor.fetchall()
            
            for col in columns:
                col_name, data_type, nullable, default = col
                nullable_str = "NULL" if nullable == "YES" else "NOT NULL"
                default_str = f" DEFAULT {default}" if default else ""
                print(f"  - {col_name}: {data_type} {nullable_str}{default_str}")
            
            # Contar registros
            cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
            count = cursor.fetchone()[0]
            print(f"  Registros: {count}")
    
    # Analizar modelos Django
    print("\n" + "=" * 80)
    print("MODELOS DJANGO ACTUALES")
    print("=" * 80)
    
    print("\nMODELO MOVIL:")
    print("-" * 20)
    movil_fields = Movil._meta.get_fields()
    for field in movil_fields:
        if hasattr(field, 'name'):
            field_type = type(field).__name__
            null_info = "NULL" if field.null else "NOT NULL"
            print(f"  - {field.name}: {field_type} ({null_info})")
    
    print("\nMODELO EQUIPO:")
    print("-" * 20)
    equipo_fields = Equipo._meta.get_fields()
    for field in equipo_fields:
        if hasattr(field, 'name'):
            field_type = type(field).__name__
            null_info = "NULL" if field.null else "NOT NULL"
            print(f"  - {field.name}: {field_type} ({null_info})")
    
    # Contar registros
    print("\nREGISTROS ACTUALES:")
    print("-" * 30)
    print(f"  - Moviles: {Movil.objects.count()}")
    print(f"  - Equipos: {Equipo.objects.count()}")
    
    # Mostrar ejemplos
    if Movil.objects.exists():
        print("\nEJEMPLO DE MOVIL:")
        movil = Movil.objects.first()
        print(f"  - ID: {movil.id}")
        print(f"  - Patente: {movil.patente}")
        print(f"  - GPS ID: {movil.gps_id}")
        print(f"  - Lat: {movil.ultimo_lat}")
        print(f"  - Lon: {movil.ultimo_lon}")
        print(f"  - Velocidad: {movil.ultima_velocidad_kmh}")
        print(f"  - Ignicion: {movil.ignicion}")
        print(f"  - Bateria: {movil.bateria_pct}")

if __name__ == "__main__":
    try:
        analyze_database()
        print("\n" + "=" * 80)
        print("ANALISIS COMPLETADO")
        print("=" * 80)
        
    except Exception as e:
        print(f"Error en el analisis: {e}")
        import traceback
        traceback.print_exc()
