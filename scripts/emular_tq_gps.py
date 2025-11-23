#!/usr/bin/env python
"""
Emulador de equipos GPS TQ
===========================

Script para simular un equipo GPS enviando posiciones al receptor TCP.
Útil para pruebas sin un equipo físico.
"""

import os
import sys
import socket
import time
import binascii
from datetime import datetime, timedelta

# Configurar Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wayproject.settings')

import django
django.setup()

from moviles.models import Movil, MovilStatus


def build_tq_message(device_id: str, fecha_gps: str, hora_gps: str) -> bytes:
    """
    Construir mensaje TQ basado en el formato real del equipo.
    
    El mensaje se basa en el ejemplo real:
    24207666813321181418092534422037060583560022002248ffffdfff000354f100000000000000df16000018
    
    Solo actualiza fecha/hora, mantiene el resto idéntico.
    
    Args:
        device_id: ID del equipo (10 dígitos)
        fecha_gps: Fecha GPS en formato DDMMYY
        hora_gps: Hora GPS en formato HHMMSS
    
    Returns:
        bytes: Mensaje TQ en formato binario
    """
    # Construir el mensaje hexadecimal con fecha y hora actualizadas
    # Formato: 24 + ID(10) + HORA(6) + FECHA(6) + [resto igual al ejemplo]
    mensaje_hex = f"24{device_id}{hora_gps}{fecha_gps}34422037060583560022002248ffffdfff000354f100000000000000df16000018"
    
    # Convertir a bytes desde hexadecimal
    return bytes.fromhex(mensaje_hex)


def emular_posicion(movil: Movil, server_host: str = 'localhost', server_port: int = 5003):
    """
    Emular una posición para un móvil.
    
    Args:
        movil: Objeto Movil
        server_host: IP del servidor receptor
        server_port: Puerto del servidor receptor
    """
    try:
        # Conectar al servidor
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((server_host, server_port))
        
        print(f"✅ Conectado al servidor {server_host}:{server_port}")
        
        # Generar posición alrededor de la última posición conocida
        # O usar una posición por defecto si no hay
        try:
            status = MovilStatus.objects.filter(movil=movil).first()
            if status and status.ultimo_lat:
                lat = status.ultimo_lat + (0.0001 if hash(movil.patente) % 2 else -0.0001)
                lon = status.ultimo_lon + (0.0001 if hash(movil.patente) % 3 else -0.0001)
            else:
                # Buenos Aires por defecto
                lat = -34.603722 + (hash(movil.patente) % 100) * 0.001
                lon = -58.381592 + (hash(movil.patente) % 100) * 0.001
        except:
            # Buenos Aires por defecto
            lat = -34.603722 + (hash(movil.patente) % 100) * 0.001
            lon = -58.381592 + (hash(movil.patente) % 100) * 0.001
        
        # Generar datos simulados
        now = datetime.now()
        fecha_gps = now.strftime('%d%m%y')
        hora_gps = now.strftime('%H%M%S')
        
        # Usar el device_id del móvil
        # El device_id puede venir en formato corto (5 dígitos, ej: "68133") o completo (10 dígitos)
        device_id_raw = movil.gps_id if movil.gps_id else "68133"
        
        # Normalizar a 10 dígitos para el mensaje TQ
        if len(device_id_raw) == 5:
            # Si viene corto (5 dígitos), rellenar al principio para hacer 10
            # Ejemplo: "68133" -> "00000068133"
            device_id = "00000" + device_id_raw  # Total: 10 dígitos
        elif len(device_id_raw) == 10:
            device_id = device_id_raw  # Ya tiene 10 dígitos
        elif len(device_id_raw) > 10:
            device_id = device_id_raw[-10:]  # Tomar los últimos 10
        else:
            device_id = device_id_raw.zfill(10)  # Rellenar con ceros
        
        # ID corto (últimos 5) para mostrar/logging
        device_id_corto = device_id[-5:]
        
        # Construir mensaje (usa el formato exacto del ejemplo real)
        message = build_tq_message(
            device_id=device_id,
            fecha_gps=fecha_gps,
            hora_gps=hora_gps
        )
        
        # Enviar mensaje
        sock.send(message)
        
        # Mostrar mensaje completo en hex
        hex_completo = binascii.hexlify(message).decode()
        
        print(f"📤 Mensaje enviado:")
        print(f"   Equipo: {movil.patente} ({movil.alias})")
        print(f"   GPS ID Completo: {device_id} (últimos 5 para RPG: {device_id_corto})")
        print(f"   Fecha GPS: {fecha_gps}, Hora GPS: {hora_gps}")
        print(f"   Hex completo ({len(message)} bytes): {hex_completo}")
        
        # Cerrar conexión
        sock.close()
        
        return True
        
    except ConnectionRefusedError:
        print(f"❌ Error: No se pudo conectar al servidor {server_host}:{server_port}")
        print(f"   Asegúrate de que el receptor TCP esté ejecutándose")
        return False
    except Exception as e:
        print(f"❌ Error enviando posición: {e}")
        return False


def main():
    """Función principal"""
    print("=" * 60)
    print("📡 EMULADOR DE EQUIPOS GPS TQ")
    print("=" * 60)
    
    import argparse
    parser = argparse.ArgumentParser(description='Emular posición GPS para un móvil')
    parser.add_argument('--patente', type=str, help='Patente del móvil a emular')
    parser.add_argument('--host', type=str, default='localhost', help='IP del servidor receptor')
    parser.add_argument('--port', type=int, default=5003, help='Puerto del servidor receptor')
    parser.add_argument('--interval', type=int, default=60, help='Intervalo entre envíos (segundos)')
    parser.add_argument('--count', type=int, default=1, help='Número de posiciones a enviar')
    
    args = parser.parse_args()
    
    # Listar móviles disponibles si no se especifica uno
    if not args.patente:
        print("\n📋 Móviles disponibles:")
        moviles = Movil.objects.all()
        for movil in moviles:
            print(f"   - {movil.patente} ({movil.alias}) - GPS ID: {movil.gps_id}")
        
        print("\nUso: python emular_tq_gps.py --patente <PATENTE>")
        print("Ejemplo: python emular_tq_gps.py --patente OVV799")
        return
    
    # Buscar el móvil
    try:
        movil = Movil.objects.get(patente=args.patente)
    except Movil.DoesNotExist:
        print(f"❌ Móvil con patente '{args.patente}' no encontrado")
        return
    
    print(f"\n🚗 Emulando posición para: {movil.patente} ({movil.alias})")
    print(f"📍 Servidor: {args.host}:{args.port}")
    print(f"⏱️  Intervalo: {args.interval} segundos")
    print(f"🔢 Envíos: {args.count}")
    print("\nPresiona Ctrl+C para detener\n")
    
    try:
        for i in range(args.count):
            print(f"\n📍 Posición #{i+1}/{args.count}")
            success = emular_posicion(movil, args.host, args.port)
            
            if not success:
                break
            
            # Esperar antes de la siguiente posición
            if i < args.count - 1:
                time.sleep(args.interval)
    
    except KeyboardInterrupt:
        print("\n🛑 Interrupción detectada")
    
    print("\n✅ Emulación completada")


if __name__ == "__main__":
    main()
