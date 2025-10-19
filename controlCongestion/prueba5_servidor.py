"""
Prueba 5: Servidor para comparación de tiempo
"""
import SocketTCP

address = ("localhost", 8001)

server_socketTCP = SocketTCP.SocketTCP()
server_socketTCP.bind(address)
print("[INFO] Servidor escuchando en", address)

connection_socketTCP, new_address = server_socketTCP.accept()
print(f"[INFO] Cliente conectado - Recibiendo archivo...")

# Recibir
data = connection_socketTCP.recv(1024, mode="go_back_n")
full_content = data

while connection_socketTCP.message_length > 0:
    data = connection_socketTCP.recv(1024, mode="go_back_n")
    full_content += data

print(f"[INFO] Recibidos {len(full_content)} bytes")

connection_socketTCP.recv_close()
print("[INFO] Listo para siguiente prueba")
