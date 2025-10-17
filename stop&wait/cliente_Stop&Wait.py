import socket
import sys
# Importamos las funciones de utils para envío por trozos
from utils import send_full_message, end_of_message

if len(sys.argv) != 3:
    sys.exit('Uso: python cliente.py <host> <puerto> < archivo.txt\nEjemplo: python cliente.py localhost 8000 < archivo.txt')

host = sys.argv[1]
port = int(sys.argv[2])
server_address = (host, port)

# Leer el contenido del archivo desde entrada estándar (stdin)
message = sys.stdin.read()

print('Creando socket - Cliente')
client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Definimos el tamaño máximo de paquete (16 bytes sin headers)
max_packet_size = 16

# Enviamos el mensaje usando send_full_message que divide en trozos de max_packet_size
message_with_end = message + end_of_message
print(f"... Enviando archivo ({len(message)} bytes) en trozos de {max_packet_size} bytes")

# Enviamos con 0% de pérdidas para Test 1
send_full_message(
    client_socket, 
    message_with_end.encode(), 
    end_of_message, 
    server_address, 
    max_packet_size, 
    message_loss_percentage=0
)

print("... Archivo enviado completamente")
client_socket.close()
