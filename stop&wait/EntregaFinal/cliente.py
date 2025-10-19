import sys
import SocketTCP

if len(sys.argv) != 3:
    print("Uso: python3 cliente.py <host> <puerto>")
    sys.exit(1)

host = sys.argv[1]
port = int(sys.argv[2])
server_address = (host, port)

# Leer datos desde stdin
data = sys.stdin.read()

# Crear socket y conectar
client_socket = SocketTCP.SocketTCP()
client_socket.connect(server_address)

# Enviar datos
print(f"[DEBUG] Enviando {len(data)} bytes")
client_socket.send(data.encode())
print("[DEBUG] Datos enviados correctamente")

# Cerrar conexión
print("[DEBUG] Cerrando conexión...")
client_socket.close()
print("[DEBUG] Conexión cerrada")
