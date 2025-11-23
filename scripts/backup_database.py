#!/usr/bin/env python
"""
Script para crear backup de la base de datos usando Django
"""

import os
import sys
import django
from datetime import datetime

# Configurar Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wayproject.settings')
django.setup()

from django.core.management import call_command
from django.db import connection

def crear_backup():
    """Crear backup de la base de datos"""
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"backup_antes_migracion_{timestamp}.json"
    
    print("=" * 80)
    print("CREANDO BACKUP DE LA BASE DE DATOS")
    print("=" * 80)
    
    try:
        # Crear backup usando Django dumpdata
        print(f"Creando backup: {backup_filename}")
        
        with open(backup_filename, 'w', encoding='utf-8') as f:
            call_command('dumpdata', 
                        'gps', 
                        'authentication', 
                        'auth', 
                        'contenttypes',
                        'sessions',
                        stdout=f,
                        indent=2)
        
        print(f"✅ Backup creado exitosamente: {backup_filename}")
        
        # Verificar tamaño del archivo
        file_size = os.path.getsize(backup_filename)
        print(f"📊 Tamaño del backup: {file_size:,} bytes ({file_size/1024/1024:.2f} MB)")
        
        # Mostrar estadísticas de la base de datos
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM moviles;")
            moviles_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM equipos_gps;")
            equipos_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM auth_user;")
            usuarios_count = cursor.fetchone()[0]
        
        print(f"\n📊 Estadísticas de la base de datos:")
        print(f"  - Móviles: {moviles_count}")
        print(f"  - Equipos GPS: {equipos_count}")
        print(f"  - Usuarios: {usuarios_count}")
        
        return backup_filename
        
    except Exception as e:
        print(f"❌ Error creando backup: {e}")
        return None

if __name__ == "__main__":
    backup_file = crear_backup()
    if backup_file:
        print(f"\n✅ Backup completado: {backup_file}")
        print("🔄 Puedes continuar con la migración")
    else:
        print("\n❌ Error en el backup. Revisa los errores antes de continuar.")
