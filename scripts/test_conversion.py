#!/usr/bin/env python
"""
Script de prueba para verificar la conversión de mensaje TQ a hexadecimal
"""

import binascii

# Mensaje real de ejemplo (en hexadecimal ASCII)
mensaje_real = "24207666813321181418092534422037060583560022002248ffffdfff000354f100000000000000df16000018"

print("=" * 80)
print("PRUEBA DE CONVERSIÓN DE MENSAJE TQ")
print("=" * 80)
print()

# 1. El mensaje tal como viene del emulador (parte ASCII + parte binaria)
print("1. Mensaje como se envía desde el emulador:")
print()

# Parte ASCII (decimal)
parte_ascii = "24207666813321181418092534422037060583560022002248ffffdfff000354f100000000000000df16000018"

# Convertir a bytes
mensaje_bytes = bytes.fromhex(parte_ascii)

print(f"   Longitud: {len(parte_ascii)} caracteres hex")
print(f"   Bytes: {len(mensaje_bytes)} bytes")
print()

# 2. La conversion que hace el receptor
print("2. Conversion que hace el receptor (bytes -> hex):")
print()

hex_resultado = binascii.hexlify(mensaje_bytes).decode('ascii')

print(f"   Resultado: {hex_resultado}")
print()

# Comparar
print("3. Comparación:")
print(f"   Original:  {mensaje_real}")
print(f"   Resultado: {hex_resultado}")
print(f"   ¿Igual?: {mensaje_real == hex_resultado}")
print()

# Mostrar estructura del mensaje
print("4. Estructura del mensaje (según get_id_ok, get_lat_chino, etc):")
print()
print(f"   Pos 0-1:   {hex_resultado[0:2]}   (Header)")
print(f"   Pos 2-11:  {hex_resultado[2:12]}  (ID Completo - {hex_resultado[2:12]})")
print(f"   Pos 12-17: {hex_resultado[12:18]} (Hora GPS)")
print(f"   Pos 18-23: {hex_resultado[18:24]} (Fecha GPS)")
print(f"   Pos 24-33: {hex_resultado[24:34]} (Latitud)")
print(f"   Pos 34-43: {hex_resultado[34:44]} (Longitud)")
print(f"   Pos 44-46: {hex_resultado[44:47]} (Velocidad)")
print(f"   Pos 47-49: {hex_resultado[47:50]} (Rumbo)")
print()

print("ID para RPG (últimos 5 del ID completo):", hex_resultado[2:12][-5:])
