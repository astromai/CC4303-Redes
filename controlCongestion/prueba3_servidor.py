"""
Prueba 3: Servidor simple para recibir con control de congestión
"""
import SocketTCP

address = ("localhost", 8001)

server_socketTCP = SocketTCP.SocketTCP()
server_socketTCP.bind(address)
print("[INFO] Servidor escuchando en", address)
print("[INFO] Esperando cliente...\n")

connection_socketTCP, new_address = server_socketTCP.accept()
print(f"[INFO] Cliente conectado desde {new_address}")
print("[INFO] Recibiendo archivo...\n")

# Recibir
data = connection_socketTCP.recv(1024, mode="go_back_n")
full_content = data

while connection_socketTCP.message_length > 0:
    data = connection_socketTCP.recv(1024, mode="go_back_n")
    full_content += data

print(f"\n[RESULTADO] Bytes recibidos: {len(full_content)}")

# Recibir señal de cierre
connection_socketTCP.recv_close()
print("[INFO] Transmisión completada")
