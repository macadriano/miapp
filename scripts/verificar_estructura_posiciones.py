#!/usr/bin/env python
"""
Script para verificar la estructura de la tabla posiciones
"""

import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wayproject.settings')
django.setup()

from django.db import connection

def verificar_estructura():
    """Verifica la estructura de la tabla posiciones"""
    
    print("🔍 Verificando estructura de la tabla posiciones...")
    
    with connection.cursor() as cursor:
        # Verificar si la tabla existe
        cursor.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_name = 'posiciones'
            ORDER BY ordinal_position;
        """)
        
        columns = cursor.fetchall()
        
        if not columns:
            print("❌ La tabla 'posiciones' no existe")
            return False
        
        print("📋 Estructura de la tabla 'posiciones':")
        for column in columns:
            print(f"   - {column[0]} ({column[1]}) - Nullable: {column[2]}")
        
        return True

if __name__ == '__main__':
    verificar_estructura()
