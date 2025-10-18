import SocketTCP

# Definir la dirección del servidor
address = ('localhost', 8000)

print("=== TEST 3-WAY HANDSHAKE - CLIENTE ===")
print(f"Conectando al servidor en {address}")

# CLIENT
client_socketTCP = SocketTCP.SocketTCP()
print("Cliente creado, iniciando handshake...")

client_socketTCP.connect(address)

print(f"¡Handshake completado!")
print(f"Conectado al servidor: {client_socketTCP.destino}")
print(f"Estado de conexión: {client_socketTCP.conectado}")
print(f"Número de secuencia: {client_socketTCP.num_seq}")