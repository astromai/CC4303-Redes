"""
Prueba 2: Integridad de datos SIN pérdidas con control de congestión
"""
import SocketTCP
import hashlib

address = ("localhost", 8001)

# Crear servidor
server_socketTCP = SocketTCP.SocketTCP()
server_socketTCP.bind(address)
print("[INFO] Servidor escuchando en", address)
print("[INFO] Esperando cliente...\n")

# Aceptar conexión
connection_socketTCP, new_address = server_socketTCP.accept()
print(f"[INFO] Cliente conectado desde {new_address}\n")

# Recibir archivo
print("[INFO] Recibiendo archivo con Go Back-N + Control de Congestión...")
data = connection_socketTCP.recv(1024, mode="go_back_n")
full_content = data

while connection_socketTCP.message_length > 0:
    data = connection_socketTCP.recv(1024, mode="go_back_n")
    full_content += data

# Calcular hash
hash_md5 = hashlib.md5(full_content).hexdigest()
print(f"\n[RESULTADO] Bytes recibidos: {len(full_content)}")
print(f"[RESULTADO] MD5: {hash_md5}")

# Recibir señal de cierre
connection_socketTCP.recv_close()

print("\n[INFO] Transmisión completada")
print("\n✓ Prueba 2 - Servidor cerrado correctamente")
