#!/usr/bin/env python
"""
Script detallado para analizar la estructura actual de la base de datos
y compararla con los requerimientos de la nueva arquitectura GPS.
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
from authentication.models import PerfilUsuario, Rol, Perfil

def analyze_database_structure():
    """Analizar estructura completa de la base de datos"""
    
    print("=" * 80)
    print("ANALISIS DETALLADO DE BASE DE DATOS - WAYGPS")
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
            print(f"\n📋 TABLA: {table_name}")
            print("=" * 50)
            
            # Obtener información detallada de la tabla
            cursor.execute(f"""
                SELECT 
                    column_name,
                    data_type,
                    is_nullable,
                    column_default,
                    character_maximum_length,
                    numeric_precision,
                    numeric_scale
                FROM information_schema.columns 
                WHERE table_name = '{table_name}'
                ORDER BY ordinal_position;
            """)
            
            columns = cursor.fetchall()
            
            for col in columns:
                col_name, data_type, nullable, default, max_length, precision, scale = col
                
                # Formatear información del campo
                nullable_str = "NULL" if nullable == "YES" else "NOT NULL"
                default_str = f" DEFAULT {default}" if default else ""
                
                # Información adicional según el tipo
                type_info = data_type
                if max_length:
                    type_info += f"({max_length})"
                elif precision and scale:
                    type_info += f"({precision},{scale})"
                elif precision:
                    type_info += f"({precision})"
                
                print(f"  • {col_name}: {type_info} {nullable_str}{default_str}")
            
            # Contar registros
            cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
            count = cursor.fetchone()[0]
            print(f"\n  📊 Registros: {count}")
            
            # Mostrar ejemplo de datos si hay registros
            if count > 0 and count <= 5:
                cursor.execute(f"SELECT * FROM {table_name} LIMIT 1;")
                sample = cursor.fetchone()
                if sample:
                    print(f"  📝 Ejemplo: {sample}")
    
    # Analizar relaciones entre tablas
    print("\n" + "=" * 80)
    print("ANALISIS DE RELACIONES")
    print("=" * 80)
    
    cursor.execute("""
        SELECT 
            tc.table_name, 
            kcu.column_name, 
            ccu.table_name AS foreign_table_name,
            ccu.column_name AS foreign_column_name 
        FROM 
            information_schema.table_constraints AS tc 
            JOIN information_schema.key_column_usage AS kcu
              ON tc.constraint_name = kcu.constraint_name
              AND tc.table_schema = kcu.table_schema
            JOIN information_schema.constraint_column_usage AS ccu
              ON ccu.constraint_name = tc.constraint_name
              AND ccu.table_schema = tc.table_schema
        WHERE tc.constraint_type = 'FOREIGN KEY' 
        AND tc.table_schema='public';
    """)
    
    foreign_keys = cursor.fetchall()
    
    if foreign_keys:
        print("\n🔗 CLAVES FORANEAS:")
        for fk in foreign_keys:
            table, column, ref_table, ref_column = fk
            print(f"  • {table}.{column} → {ref_table}.{ref_column}")
    else:
        print("\n⚠️  No se encontraron claves foráneas")
    
    # Analizar índices
    print("\n" + "=" * 80)
    print("ANALISIS DE INDICES")
    print("=" * 80)
    
    cursor.execute("""
        SELECT 
            schemaname,
            tablename,
            indexname,
            indexdef
        FROM pg_indexes 
        WHERE schemaname = 'public'
        ORDER BY tablename, indexname;
    """)
    
    indexes = cursor.fetchall()
    
    if indexes:
        print("\n📇 INDICES EXISTENTES:")
        for idx in indexes:
            schema, table, name, definition = idx
            print(f"  • {table}.{name}: {definition}")
    else:
        print("\n⚠️  No se encontraron índices personalizados")

def analyze_django_models():
    """Analizar modelos Django actuales"""
    
    print("\n" + "=" * 80)
    print("ANALISIS DE MODELOS DJANGO")
    print("=" * 80)
    
    # Modelo Movil
    print("\n📱 MODELO MOVIL:")
    print("-" * 30)
    movil_fields = Movil._meta.get_fields()
    for field in movil_fields:
        if hasattr(field, 'name'):
            field_type = type(field).__name__
            null_info = "NULL" if field.null else "NOT NULL"
            unique_info = " UNIQUE" if field.unique else ""
            print(f"  • {field.name}: {field_type} ({null_info}){unique_info}")
    
    # Modelo Equipo
    print("\n🔧 MODELO EQUIPO:")
    print("-" * 30)
    equipo_fields = Equipo._meta.get_fields()
    for field in equipo_fields:
        if hasattr(field, 'name'):
            field_type = type(field).__name__
            null_info = "NULL" if field.null else "NOT NULL"
            unique_info = " UNIQUE" if field.unique else ""
            print(f"  • {field.name}: {field_type} ({null_info}){unique_info}")
    
    # Modelos de autenticación
    print("\n👤 MODELOS DE AUTENTICACION:")
    print("-" * 30)
    
    try:
        perfil_fields = PerfilUsuario._meta.get_fields()
        print("  📋 PerfilUsuario:")
        for field in perfil_fields:
            if hasattr(field, 'name'):
                field_type = type(field).__name__
                print(f"    • {field.name}: {field_type}")
    except:
        print("  ⚠️  PerfilUsuario no disponible")
    
    try:
        rol_fields = Rol._meta.get_fields()
        print("  📋 Rol:")
        for field in rol_fields:
            if hasattr(field, 'name'):
                field_type = type(field).__name__
                print(f"    • {field.name}: {field_type}")
    except:
        print("  ⚠️  Rol no disponible")

def generate_comparison_report():
    """Generar reporte de comparación con nueva arquitectura"""
    
    print("\n" + "=" * 80)
    print("REPORTE DE COMPARACION CON NUEVA ARQUITECTURA")
    print("=" * 80)
    
    print("\n✅ CAMPOS EXISTENTES QUE SE MANTIENEN:")
    print("-" * 50)
    existing_gps_fields = [
        "ultimo_lat", "ultimo_lon", "ultima_velocidad_kmh", 
        "ultimo_rumbo", "fecha_gps", "fecha_recepcion",
        "ignicion", "bateria_pct", "satelites", "hdop"
    ]
    
    for field in existing_gps_fields:
        print(f"  ✓ {field}")
    
    print("\n🆕 CAMPOS NUEVOS NECESARIOS:")
    print("-" * 50)
    new_fields = [
        "estado_conexion (conectado/desconectado/error)",
        "calidad_senal (numero de satelites)",
        "ultima_actualizacion (timestamp)",
        "ignicion_estado (boolean mejorado)"
    ]
    
    for field in new_fields:
        print(f"  + {field}")
    
    print("\n📊 NUEVAS TABLAS NECESARIAS:")
    print("-" * 50)
    new_tables = [
        "posiciones_historicas (histórico de posiciones)",
        "tipos_equipos_gps (Teltonika, Queclink, etc.)",
        "configuraciones_receptores (puertos y configuraciones)",
        "estadisticas_recepcion (métricas del sistema)",
        "sesiones_usuarios (sesiones activas)",
        "permisos_entidad (permisos por entidad)"
    ]
    
    for table in new_tables:
        print(f"  + {table}")
    
    print("\n🔧 NUEVAS APPS NECESARIAS:")
    print("-" * 50)
    new_apps = [
        "data_ingestion (receptores GPS)",
        "realtime (WebSockets)",
        "monitoring (monitoreo del sistema)"
    ]
    
    for app in new_apps:
        print(f"  + {app}")

if __name__ == "__main__":
    try:
        analyze_database_structure()
        analyze_django_models()
        generate_comparison_report()
        
        print("\n" + "=" * 80)
        print("✅ ANALISIS COMPLETADO")
        print("=" * 80)
        print("\nPróximos pasos:")
        print("1. Revisar el Excel 'DER BASE DATOS WAY.xlsx'")
        print("2. Comparar con la estructura actual")
        print("3. Crear plan de migración detallado")
        print("4. Implementar cambios paso a paso")
        
    except Exception as e:
        print(f"❌ Error en el análisis: {e}")
        import traceback
        traceback.print_exc()
