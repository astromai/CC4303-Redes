import SocketTCP

# Definir la dirección del servidor
address = ('localhost', 8000)

print("=== TEST 3-WAY HANDSHAKE - SERVIDOR ===")
print(f"Iniciando servidor en {address}")

# SERVER
server_socketTCP = SocketTCP.SocketTCP()
server_socketTCP.bind(address)
print(f"Servidor vinculado a {address}")
print("Esperando conexión del cliente...")

connection_socketTCP, new_address = server_socketTCP.accept()

if connection_socketTCP:
    print(f"¡Handshake exitoso!")
    print(f"Nueva conexión creada en dirección: {new_address}")
    print(f"Cliente conectado desde: {connection_socketTCP.destino}")
    print(f"Estado de conexión: {connection_socketTCP.conectado}")
    print(f"Número de secuencia: {connection_socketTCP.num_seq}")
else:
    print("Error en el handshake")