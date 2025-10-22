import SocketTCP

# Configuración
address = ("localhost", 8001)

print("[SERVIDOR] Iniciando servidor...")

# Crear servidor
server_socketTCP = SocketTCP.SocketTCP()
server_socketTCP.bind(address)
print(f"[SERVIDOR] Escuchando en {address}")
print("[SERVIDOR] Esperando conexión del cliente...\n")

# Aceptar conexión
connection_socketTCP, new_address = server_socketTCP.accept()
print(f"[SERVIDOR] Cliente conectado desde {new_address}")
print("[SERVIDOR] Recibiendo datos...\n")

# Primer recv para obtener el message_length automáticamente
# y empezar a recibir datos
data = connection_socketTCP.recv(16, mode="go_back_n")
full_content = data

# Seguir recibiendo hasta que message_length y bytes_received coincidan
# (cuando bytes_received >= message_length, recv() resetea las variables)
while connection_socketTCP.message_length > 0:
    data = connection_socketTCP.recv(16, mode="go_back_n")
    full_content += data

print(f"[SERVIDOR] Recepción completa: {len(full_content)} bytes\n")

# Mostrar contenido recibido
print("="*80)
print("[SERVIDOR] CONTENIDO RECIBIDO:")
print("="*80)
print(full_content.decode())
print("="*80 + "\n")

# Cerrar conexión
print("[SERVIDOR] Esperando FIN del cliente...")
connection_socketTCP.recv_close()
print("[SERVIDOR] Conexión cerrada\n")
