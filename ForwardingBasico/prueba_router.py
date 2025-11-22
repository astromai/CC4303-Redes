import sys
import socket

# Validar argumentos
if len(sys.argv) != 5:
    print("Uso: python3 prueba_router.py <headers> <IP_router_inicial> <puerto_router_inicial> <archivo>")
    print("Ejemplo: python3 prueba_router.py \"127.0.0.1;8885;10\" 127.0.0.1 8881 archivo.txt")
    sys.exit(1)

# Obtener parámetros
headers = sys.argv[1]  # Formato: IP_destino;puerto_destino;TTL
router_inicial_IP = sys.argv[2]
router_inicial_puerto = int(sys.argv[3])
filename = sys.argv[4]

# Parsear headers
header_parts = headers.split(';')
if len(header_parts) != 3:
    print("Error: Los headers deben tener el formato IP;puerto;TTL")
    sys.exit(1)

dest_ip = header_parts[0]
dest_puerto = header_parts[1]
ttl = header_parts[2]

print(f"Enviando paquetes a destino {dest_ip}:{dest_puerto} con TTL={ttl}")
print(f"Router inicial: {router_inicial_IP}:{router_inicial_puerto}")
print(f"Archivo: {filename}\n")

# Crear socket UDP
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

try:
    # Leer archivo línea por línea
    with open(filename, 'r') as file:
        linea_numero = 1
        for linea in file:
            linea = linea.rstrip('\n')  # Eliminar salto de línea
            
            # Crear paquete: IP;puerto;TTL;mensaje
            paquete = f"{dest_ip};{dest_puerto};{ttl};{linea}"
            
            # Enviar paquete
            sock.sendto(paquete.encode(), (router_inicial_IP, router_inicial_puerto))
            print(f"Enviado paquete {linea_numero}: {linea[:50]}{'...' if len(linea) > 50 else ''}")
            linea_numero += 1
    
    print(f"\nTotal de líneas enviadas: {linea_numero - 1}")

except FileNotFoundError:
    print(f"Error: No se encontró el archivo '{filename}'")
except Exception as e:
    print(f"Error: {e}")
finally:
    sock.close()
