import SocketTCP

# Definir la dirección del servidor
address = ('localhost', 8000)

print("=== TEST SEND & RECV - CLIENTE ===")

# CLIENT
client_socketTCP = SocketTCP.SocketTCP()
client_socketTCP.connect(address)

print("Conexión establecida, enviando mensajes de test...")

# test 1
message = "Mensje de len=16".encode()
print(f"Enviando test 1: {message}")
client_socketTCP.send(message)
print("Test 1 enviado")

# test 2
message = "Mensaje de largo 19".encode()
print(f"Enviando test 2: {message}")
client_socketTCP.send(message)
print("Test 2 enviado")

# test 3
message = "Mensaje de largo 19".encode()
print(f"Enviando test 3: {message}")
client_socketTCP.send(message)
print("Test 3 enviado")

print("Todos los mensajes enviados")

# Test de cierre de conexión
print("\n=== TEST CIERRE DE CONEXIÓN ===")
print("Iniciando cierre de conexión...")
client_socketTCP.close()
print("¡Cierre de conexión exitoso!")