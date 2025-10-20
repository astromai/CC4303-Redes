import SocketTCP

# Configuración
address = ("localhost", 8001)

# Crear servidor
server_socketTCP = SocketTCP.SocketTCP()
server_socketTCP.bind(address)
print(f"[DEBUG] Servidor escuchando en {address}")

print("\n=== TEST HANDSHAKE ===")
print("[DEBUG] Esperando handshake con cliente...")
connection_socketTCP, new_address = server_socketTCP.accept()
print(f"[DEBUG] Handshake completado exitosamente")
print(f"[DEBUG] Cliente conectado desde {new_address}")
print(f"[DEBUG] Número de secuencia inicial del servidor: {connection_socketTCP.num_seq}")
print(f"[DEBUG] Estado de conexión: {connection_socketTCP.conectado}")
print()

# Test 1: Recibir mensaje de 16 bytes
print("=== TEST 1: Recibir 16 bytes ===")
buff_size = 16
print(f"[DEBUG] Esperando mensaje con buff_size={buff_size}")
full_message = connection_socketTCP.recv(buff_size)
print(f"[DEBUG] Recibido: {full_message}")
if full_message == "Mensje de len=16".encode():
    print("Test 1: PASSED")
else:
    print("Test 1: FAILED")
    print(f"  Esperado: {'Mensje de len=16'.encode()}")
    print(f"  Recibido: {full_message}")
print()

# Test 2: Recibir mensaje de 19 bytes
print("=== TEST 2: Recibir 19 bytes ===")
buff_size = 19
print(f"[DEBUG] Esperando mensaje con buff_size={buff_size}")
full_message = connection_socketTCP.recv(buff_size)
print(f"[DEBUG] Recibido: {full_message}")
if full_message == "Mensaje de largo 19".encode():
    print("Test 2: PASSED")
else:
    print("Test 2: FAILED")
    print(f"  Esperado: {'Mensaje de largo 19'.encode()}")
    print(f"  Recibido: {full_message}")
print()

# Test 3: Recibir mensaje de 19 bytes en dos llamadas (14 + 5)
print("=== TEST 3: Recibir 19 bytes en dos partes (14 + 5) ===")
buff_size = 14
print(f"[DEBUG] Primera llamada recv con buff_size={buff_size}")
message_part_1 = connection_socketTCP.recv(buff_size)
print(f"[DEBUG] Parte 1 recibida: {message_part_1} ({len(message_part_1)} bytes)")

print(f"[DEBUG] Segunda llamada recv con buff_size={buff_size}")
message_part_2 = connection_socketTCP.recv(buff_size)
print(f"[DEBUG] Parte 2 recibida: {message_part_2} ({len(message_part_2)} bytes)")

full_message = message_part_1 + message_part_2
print(f"[DEBUG] Mensaje completo: {full_message}")
if full_message == "Mensaje de largo 19".encode():
    print("Test 3: PASSED")
else:
    print("Test 3: FAILED")
    print(f"  Esperado: {'Mensaje de largo 19'.encode()}")
    print(f"  Recibido: {full_message}")
print()

# Cerrar conexión
print("=== CERRANDO CONEXIÓN ===")
print("[DEBUG] Esperando cierre iniciado por cliente...")
connection_socketTCP.recv_close()
print("[DEBUG] Conexión cerrada correctamente")
