#!/usr/bin/env python
"""
Script para verificar qué receptores están activos en la BD
"""

import os
import sys
import django

# Configurar Django
sys.path.insert(0, '/opt/miapp')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wayproject.settings')
django.setup()

from gps.models import ConfiguracionReceptor

print("=" * 60)
print("RECEPTORES CONFIGURADOS EN LA BASE DE DATOS")
print("=" * 60)

receptores = ConfiguracionReceptor.objects.all().order_by('puerto')

if not receptores.exists():
    print("❌ No hay receptores configurados en la BD")
else:
    print(f"\nTotal de receptores: {receptores.count()}\n")
    
    for receptor in receptores:
        estado = "✅ ACTIVO" if receptor.activo else "❌ INACTIVO"
        print(f"Puerto: {receptor.puerto:5d} | {estado:12s} | Nombre: {receptor.nombre}")
        print(f"         Tipo: {receptor.tipo_equipo.nombre if receptor.tipo_equipo else 'N/A'}")
        print(f"         Transporte: {receptor.transporte}")
        print()

print("=" * 60)
print("RECEPTORES ACTIVOS (se iniciarán automáticamente)")
print("=" * 60)

receptores_activos = ConfiguracionReceptor.objects.filter(activo=True).order_by('puerto')

if not receptores_activos.exists():
    print("❌ No hay receptores activos")
else:
    print(f"\nTotal de receptores activos: {receptores_activos.count()}\n")
    for receptor in receptores_activos:
        print(f"✅ Puerto {receptor.puerto}: {receptor.nombre}")

print("\n" + "=" * 60)
print("PARA ACTIVAR/DESACTIVAR RECEPTORES:")
print("=" * 60)
print("Desde el shell de Django:")
print("  python manage.py shell")
print("")
print("  from gps.models import ConfiguracionReceptor")
print("  # Activar puerto 5005")
print("  receptor = ConfiguracionReceptor.objects.get(puerto=5005)")
print("  receptor.activo = True")
print("  receptor.save()")
print("")
print("  # Desactivar otros puertos")
print("  ConfiguracionReceptor.objects.filter(puerto__in=[5008, 5009]).update(activo=False)")

