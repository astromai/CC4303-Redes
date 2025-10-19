import SocketTCP

# Configuración
address = ("localhost", 8001)

# Crear servidor
server_socketTCP = SocketTCP.SocketTCP()
server_socketTCP.bind(address)
print(f"[INFO] Servidor escuchando en {address}")
print("[INFO] Esperando conexión del cliente...\n")

# Aceptar conexión
connection_socketTCP, new_address = server_socketTCP.accept()
print(f"[INFO] Cliente conectado desde {new_address}")
print("[INFO] Recibiendo mensaje con Go Back-N...\n")

# Primer recv para obtener el message_length automáticamente
data = connection_socketTCP.recv(16, mode="go_back_n")
full_content = data

# Seguir recibiendo hasta completar
while connection_socketTCP.message_length > 0:
    data = connection_socketTCP.recv(16, mode="go_back_n")
    full_content += data

print("="*80)
print("[INFO] Mensaje recibido completo:")
print("="*80)
print(full_content.decode())
print("="*80)
print(f"\n[INFO] Total bytes recibidos: {len(full_content)}")

# Cerrar conexión
connection_socketTCP.recv_close()
print("\n[INFO] Conexión cerrada")
