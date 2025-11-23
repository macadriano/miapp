#!/usr/bin/env python
"""
Script para actualizar la estructura de la tabla posiciones a la estructura completa
"""

import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wayproject.settings')
django.setup()

from django.db import connection

def actualizar_estructura_posiciones():
    """Actualiza la estructura de la tabla posiciones"""
    
    print("🔧 Actualizando estructura de la tabla posiciones...")
    
    with connection.cursor() as cursor:
        # Verificar si la tabla existe
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'posiciones'
            );
        """)
        
        tabla_existe = cursor.fetchone()[0]
        
        if not tabla_existe:
            print("❌ La tabla 'posiciones' no existe")
            return False
        
        print("📋 Tabla 'posiciones' encontrada")
        
        # Crear backup de la tabla actual
        print("💾 Creando backup de la tabla actual...")
        cursor.execute("""
            CREATE TABLE posiciones_backup AS 
            SELECT * FROM posiciones;
        """)
        print("✅ Backup creado como 'posiciones_backup'")
        
        # Eliminar la tabla actual
        print("🗑️  Eliminando tabla actual...")
        cursor.execute("DROP TABLE posiciones CASCADE;")
        print("✅ Tabla eliminada")
        
        # Crear la nueva tabla con la estructura correcta
        print("🏗️  Creando nueva tabla con estructura completa...")
        cursor.execute("""
            CREATE TABLE posiciones (
                id BIGSERIAL PRIMARY KEY,
                
                -- Relaciones (normalización)
                empresa_id BIGINT NOT NULL,
                device_id BIGINT NOT NULL,
                movil_id BIGINT,
                evt_tipo_id SMALLINT,
                
                -- Fechas y eventos
                fec_gps TIMESTAMP,
                fec_report TIMESTAMP,
                evento VARCHAR(10),
                
                -- Datos GPS
                velocidad SMALLINT,
                rumbo SMALLINT,
                lat DECIMAL(10,7),
                lon DECIMAL(10,7),
                altitud INTEGER,
                
                -- Calidad/señal
                sats SMALLINT,
                hdop DECIMAL(4,2),
                accuracy_m INTEGER,
                
                -- Estado del vehículo
                ign_on BOOLEAN,
                batt_mv INTEGER,
                ext_pwr_mv INTEGER,
                inputs_mask VARCHAR(20),
                outputs_mask VARCHAR(20),
                
                -- Identificadores del mensaje
                msg_uid VARCHAR(64),
                seq INTEGER,
                
                -- Proveedor/protocolo
                provider VARCHAR(32),
                protocol VARCHAR(32),
                
                -- Crudo para trazabilidad
                raw_payload TEXT,
                
                -- Flags de calidad
                is_valid BOOLEAN NOT NULL DEFAULT TRUE,
                is_late BOOLEAN NOT NULL DEFAULT FALSE,
                is_duplicate BOOLEAN NOT NULL DEFAULT FALSE,
                
                -- Auditoría
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            );
        """)
        print("✅ Nueva tabla creada")
        
        # Crear índices para optimizar consultas
        print("📊 Creando índices...")
        cursor.execute("""
            CREATE INDEX idx_posiciones_empresa_fec_gps ON posiciones(empresa_id, fec_gps);
            CREATE INDEX idx_posiciones_device_fec_gps ON posiciones(device_id, fec_gps);
            CREATE INDEX idx_posiciones_movil_fec_gps ON posiciones(movil_id, fec_gps);
            CREATE INDEX idx_posiciones_fec_gps ON posiciones(fec_gps);
            CREATE INDEX idx_posiciones_velocidad ON posiciones(velocidad);
            CREATE INDEX idx_posiciones_ign_on ON posiciones(ign_on);
            CREATE INDEX idx_posiciones_is_valid ON posiciones(is_valid);
        """)
        print("✅ Índices creados")
        
        # Crear constraint para empresa_id (si la tabla empresa existe)
        try:
            cursor.execute("""
                ALTER TABLE posiciones 
                ADD CONSTRAINT fk_posiciones_empresa 
                FOREIGN KEY (empresa_id) REFERENCES empresa(id);
            """)
            print("✅ Constraint de empresa_id creado")
        except Exception as e:
            print(f"⚠️  No se pudo crear constraint de empresa_id: {e}")
        
        # Crear constraint para movil_id
        try:
            cursor.execute("""
                ALTER TABLE posiciones 
                ADD CONSTRAINT fk_posiciones_movil 
                FOREIGN KEY (movil_id) REFERENCES moviles(id);
            """)
            print("✅ Constraint de movil_id creado")
        except Exception as e:
            print(f"⚠️  No se pudo crear constraint de movil_id: {e}")
        
        print("\n🎉 Estructura de la tabla 'posiciones' actualizada exitosamente!")
        print("📋 Nueva estructura:")
        print("   - Campos completos para sistema SaaS multi-tenant")
        print("   - Campos de calidad de señal y precisión")
        print("   - Campos de estado del vehículo")
        print("   - Campos de trazabilidad y auditoría")
        print("   - Índices optimizados para consultas")
        print("   - Backup disponible en 'posiciones_backup'")
        
        return True

if __name__ == '__main__':
    try:
        actualizar_estructura_posiciones()
    except Exception as e:
        print(f"❌ Error actualizando estructura: {str(e)}")
        import traceback
        traceback.print_exc()
