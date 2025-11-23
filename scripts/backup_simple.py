#!/usr/bin/env python
"""
Script simple para crear backup de datos críticos
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

def crear_backup_simple():
    """Crear backup simple de datos críticos"""
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"backup_simple_{timestamp}.json"
    
    print("=" * 80)
    print("CREANDO BACKUP SIMPLE DE DATOS CRITICOS")
    print("=" * 80)
    
    try:
        # Crear backup solo de datos críticos
        print(f"Creando backup: {backup_filename}")
        
        with open(backup_filename, 'w', encoding='utf-8') as f:
            call_command('dumpdata', 
                        'gps.movil',
                        'gps.equipo', 
                        'auth.user',
                        'authtoken.token',
                        stdout=f,
                        indent=2)
        
        print(f"Backup creado exitosamente: {backup_filename}")
        
        # Verificar tamaño del archivo
        file_size = os.path.getsize(backup_filename)
        print(f"Tamaño del backup: {file_size:,} bytes")
        
        # Mostrar estadísticas
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM moviles;")
            moviles_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM equipos_gps;")
            equipos_count = cursor.fetchone()[0]
        
        print(f"Estadísticas:")
        print(f"  - Móviles: {moviles_count}")
        print(f"  - Equipos GPS: {equipos_count}")
        
        return backup_filename
        
    except Exception as e:
        print(f"Error creando backup: {e}")
        return None

if __name__ == "__main__":
    backup_file = crear_backup_simple()
    if backup_file:
        print(f"Backup completado: {backup_file}")
    else:
        print("Error en el backup")
