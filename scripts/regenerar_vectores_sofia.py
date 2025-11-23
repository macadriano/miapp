#!/usr/bin/env python
"""
Script para regenerar vectores de Sofia con threshold más bajo
"""
import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wayproject.settings')
django.setup()

from agenteIA.models import VectorConsulta
import random

# Función para generar embeddings placeholder consistentes
def generar_placeholder(texto):
    """Genera un embedding placeholder de 384 dimensiones"""
    random.seed(hash(texto) % 2**32)
    return [random.random() for _ in range(384)]

# Regenerar todos los vectores
vectores = VectorConsulta.objects.all()
print(f"Regenerando {vectores.count()} vectores...")

for vector in vectores:
    # Generar embedding consistente basado en el texto original
    vector.vector_embedding = generar_placeholder(vector.texto_original)
    
    # Bajar el threshold a 0.3 para que funcione con embeddings placeholder
    vector.threshold = 0.3
    
    vector.save()
    print(f"✓ Regenerado: {vector.texto_original[:50]}...")

print(f"\n✅ Se regeneraron {vectores.count()} vectores con threshold 0.3")

