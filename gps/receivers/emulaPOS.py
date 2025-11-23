import socket

HOST = '127.0.0.1'
PORT = 5003  # reemplazá por el puerto del receptor

# Mensaje en formato hexadecimal ASCII (como viene del protocolo TQ)
# Este mensaje contiene: header, ID, fecha/hora GPS, coordenadas, velocidad, rumbo, etc.
mensaje_hex_ascii = '24207666813312154518092534416956060583529692001126ffffdfff000320a000000000000000df1600000c'

# Convertir el string hexadecimal a bytes reales
# El receptor espera bytes, no un string ASCII que representa hexadecimal
mensaje_bytes = bytes.fromhex(mensaje_hex_ascii)

print(f"Mensaje hexadecimal (ASCII): {mensaje_hex_ascii}")
print(f"Mensaje convertido a bytes: {mensaje_bytes.hex()}")
print(f"Longitud: {len(mensaje_bytes)} bytes")

with socket.create_connection((HOST, PORT)) as s:
    s.sendall(mensaje_bytes)
    print(f"✅ Mensaje enviado al receptor en {HOST}:{PORT}")
    
    # si el receptor responde algo, podés leerlo:
    try:
        data = s.recv(1024)
        if data:
            print("Respuesta:", data)
        else:
            print("Sin respuesta del receptor")
    except Exception as e:
        print("Sin respuesta o conexión cerrada:", e)