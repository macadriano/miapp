import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wayproject.settings')
try:
    django.setup()
except Exception as e:
    print(f"❌ Error configurando Django: {e}")
    sys.exit(1)

from decouple import config
from django.db import connection

print("\n=== DIAGNÓSTICO DE WAYGPS ===")

# 1. Verificar Variables de Entorno
print("\n1. VARIABLES DE ENTORNO:")
print(f"   DEBUG: {config('DEBUG', default='No definido')}")
print(f"   SOFIA_LITE_MODE: {config('SOFIA_LITE_MODE', default='No definido')}")
print(f"   DB_HOST: {config('DB_HOST', default='No definido')}")
print(f"   DB_NAME: {config('DB_NAME', default='No definido')}")

# 2. Verificar Base de Datos
print("\n2. CONEXIÓN A BASE DE DATOS:")
try:
    connection.ensure_connection()
    print("   ✅ Conexión exitosa.")
    
    # Probar una consulta simple
    from django.contrib.auth.models import User
    count = User.objects.count()
    print(f"   ✅ Consulta exitosa (Usuarios: {count})")
except Exception as e:
    print(f"   ❌ Error de conexión: {e}")

# 3. Verificar Dependencias de IA
print("\n3. DEPENDENCIAS DE IA:")
try:
    import numpy
    print(f"   ✅ numpy: Instalado (v{numpy.__version__})")
except ImportError:
    print("   ⚠️ numpy: No instalado")
except Exception as e:
    print(f"   ❌ numpy: Error al importar ({e})")

try:
    import sentence_transformers
    print("   ✅ sentence_transformers: Instalado")
except ImportError:
    print("   ⚠️ sentence_transformers: No instalado")
except Exception as e:
    print(f"   ❌ sentence_transformers: Error al importar ({e})")

# 4. Probar Vectorizador (Simular lo que hace Sofia)
print("\n4. PRUEBA DE VECTORIZADOR:")
try:
    from agenteIA.vectorizador import VectorizadorConsultas
    print("   Instanciando VectorizadorConsultas...")
    v = VectorizadorConsultas()
    
    print("   Vectorizando texto de prueba 'hola'...")
    vec = v.vectorizar("hola")
    
    print(f"   ✅ Vectorización exitosa.")
    print(f"   Longitud del vector: {len(vec)}")
    print(f"   ¿Modelo pesado cargado?: {'SÍ' if v.modelo else 'NO (Modo Ligero/Placeholder)'}")
    
    if len(vec) > 0:
        print("   ✅ El sistema de IA parece funcionar correctamente.")
    else:
        print("   ❌ El vector está vacío.")
        
except Exception as e:
    print(f"   ❌ Error CRÍTICO en Vectorizador: {e}")
    import traceback
    traceback.print_exc()

print("\n=== FIN DEL DIAGNÓSTICO ===")
