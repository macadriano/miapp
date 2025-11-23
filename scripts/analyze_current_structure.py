#!/usr/bin/env python
"""
Script para analizar la estructura actual de la base de datos
y compararla con la nueva arquitectura GPS en tiempo real.
"""

import os
import sys
import django
from django.conf import settings

# Configurar Django
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wayproject.settings')
django.setup()

from django.db import connection
from gps.models import Movil, Equipo

def analyze_current_structure():
    """Analizar estructura actual de la base de datos"""
    
    print("=" * 80)
    print("ANÁLISIS DE ESTRUCTURA ACTUAL - WAYGPS")
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
        
        print(f"\n📊 TABLAS EXISTENTES ({len(tables)}):")
        print("-" * 50)
        
        for table in tables:
            table_name = table[0]
            print(f"  • {table_name}")
            
            # Analizar campos de cada tabla
            cursor.execute(f"""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns 
                WHERE table_name = '{table_name}'
                ORDER BY ordinal_position;
            """)
            
            columns = cursor.fetchall()
            print(f"    Campos ({len(columns)}):")
            
            for col in columns:
                col_name, data_type, nullable, default = col
                nullable_str = "NULL" if nullable == "YES" else "NOT NULL"
                default_str = f" DEFAULT {default}" if default else ""
                print(f"      - {col_name}: {data_type} {nullable_str}{default_str}")
            
            print()
    
    # Analizar modelos Django actuales
    print("\n🔍 MODELOS DJANGO ACTUALES:")
    print("-" * 50)
    
    # Modelo Movil
    print("\n📱 MODELO MOVIL:")
    movil_fields = Movil._meta.get_fields()
    for field in movil_fields:
        if hasattr(field, 'name'):
            field_type = type(field).__name__
            null_info = "NULL" if field.null else "NOT NULL"
            print(f"  - {field.name}: {field_type} ({null_info})")
    
    # Modelo Equipo
    print("\n🔧 MODELO EQUIPO:")
    equipo_fields = Equipo._meta.get_fields()
    for field in equipo_fields:
        if hasattr(field, 'name'):
            field_type = type(field).__name__
            null_info = "NULL" if field.null else "NOT NULL"
            print(f"  - {field.name}: {field_type} ({null_info})")
    
    # Contar registros
    print("\n📈 REGISTROS ACTUALES:")
    print("-" * 50)
    print(f"  • Móviles: {Movil.objects.count()}")
    print(f"  • Equipos: {Equipo.objects.count()}")
    
    # Verificar datos de ejemplo
    if Movil.objects.exists():
        print("\n📋 EJEMPLO DE MÓVIL:")
        movil = Movil.objects.first()
        print(f"  - ID: {movil.id}")
        print(f"  - Patente: {movil.patente}")
        print(f"  - GPS ID: {movil.gps_id}")
        print(f"  - Última lat: {movil.ultimo_lat}")
        print(f"  - Última lon: {movil.ultimo_lon}")
        print(f"  - Velocidad: {movil.ultima_velocidad_kmh}")
    
    if Equipo.objects.exists():
        print("\n📋 EJEMPLO DE EQUIPO:")
        equipo = Equipo.objects.first()
        print(f"  - ID: {equipo.id}")
        print(f"  - IMEI: {equipo.imei}")
        print(f"  - Marca: {equipo.marca}")
        print(f"  - Modelo: {equipo.modelo}")
        print(f"  - Estado: {equipo.estado}")

def generate_migration_plan():
    """Generar plan de migración"""
    
    print("\n" + "=" * 80)
    print("PLAN DE MIGRACIÓN A ARQUITECTURA GPS TIEMPO REAL")
    print("=" * 80)
    
    print("\n🎯 NUEVAS TABLAS A CREAR:")
    print("-" * 50)
    new_tables = [
        "posiciones_historicas",
        "tipos_equipos_gps", 
        "configuraciones_receptores",
        "estadisticas_recepcion",
        "sesiones_usuarios",
        "permisos_entidad"
    ]
    
    for table in new_tables:
        print(f"  ✓ {table}")
    
    print("\n🔄 MODIFICACIONES A TABLAS EXISTENTES:")
    print("-" * 50)
    print("  • moviles:")
    print("    - Agregar: estado_conexion, calidad_senal, bateria_porcentaje")
    print("    - Agregar: ignicion_estado, ultima_actualizacion")
    print("    - Modificar: campos de timestamp")
    
    print("\n  • equipos_gps:")
    print("    - Agregar: ultima_comunicacion")
    print("    - Modificar: campos de timestamp")
    
    print("\n📦 NUEVAS APPS DJANGO:")
    print("-" * 50)
    new_apps = [
        "data_ingestion (receptores GPS)",
        "realtime (WebSockets)", 
        "monitoring (monitoreo del sistema)"
    ]
    
    for app in new_apps:
        print(f"  ✓ {app}")
    
    print("\n🔧 NUEVOS COMPONENTES:")
    print("-" * 50)
    components = [
        "Receptores GPS (Teltonika, Genérico)",
        "Procesadores de datos",
        "Validadores de datos", 
        "Gestor de posiciones",
        "Sistema WebSockets",
        "Frontend tiempo real",
        "Servicio de notificaciones"
    ]
    
    for component in components:
        print(f"  ✓ {component}")

if __name__ == "__main__":
    try:
        analyze_current_structure()
        generate_migration_plan()
        
        print("\n" + "=" * 80)
        print("✅ ANÁLISIS COMPLETADO")
        print("=" * 80)
        print("\nPróximos pasos:")
        print("1. Revisar el análisis anterior")
        print("2. Compartir el Excel con estructura de tablas")
        print("3. Crear plan de migración detallado")
        print("4. Implementar cambios paso a paso")
        
    except Exception as e:
        print(f"❌ Error en el análisis: {e}")
        import traceback
        traceback.print_exc()
