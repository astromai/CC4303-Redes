import SocketTCP

# Configuración
address = ("localhost", 8001)

# Crear cliente
client_socketTCP = SocketTCP.SocketTCP()

print("\n=== TEST HANDSHAKE ===")
print("[DEBUG] Iniciando handshake con servidor...")
client_socketTCP.connect(address)
print("[DEBUG] ✓ Handshake completado exitosamente")
print(f"[DEBUG] Conectado a {client_socketTCP.destino}")
print(f"[DEBUG] Número de secuencia inicial del cliente: {client_socketTCP.num_seq}")
print(f"[DEBUG] Estado de conexión: {client_socketTCP.conectado}")
print()

input("Presione Enter para ejecutar Test 1...")

# Test 1: Mensaje de exactamente 16 bytes (Go Back-N)
print("\n=== TEST 1: Mensaje de 16 bytes (Go Back-N) ===")
message = "Mensje de len=16".encode()
print(f"[DEBUG] Enviando: {message} ({len(message)} bytes)")
client_socketTCP.send(message, mode="go_back_n")
print("[DEBUG] Test 1 enviado\n")

input("Presione Enter para ejecutar Test 2...")

# Test 2: Mensaje de 19 bytes (Go Back-N)
print("\n=== TEST 2: Mensaje de 19 bytes (Go Back-N) ===")
message = "Mensaje de largo 19".encode()
print(f"[DEBUG] Enviando: {message} ({len(message)} bytes)")
print(f"[DEBUG] Estado antes de enviar - conectado: {client_socketTCP.conectado}, num_seq: {client_socketTCP.num_seq}")
client_socketTCP.send(message, mode="go_back_n")
print("[DEBUG] Test 2 enviado\n")

input("Presione Enter para ejecutar Test 3...")

# Test 3: Mismo mensaje pero será recibido en dos partes (Go Back-N)
print("\n=== TEST 3: Mensaje de 19 bytes - recv en 2 partes (Go Back-N) ===")
message = "Mensaje de largo 19".encode()
print(f"[DEBUG] Enviando: {message} ({len(message)} bytes)")
client_socketTCP.send(message, mode="go_back_n")
print("[DEBUG] Test 3 enviado\n")

input("Presione Enter para cerrar conexión...")

# Cerrar conexión
print("\n=== CERRANDO CONEXIÓN ===")
print("[DEBUG] Iniciando cierre...")
client_socketTCP.close()
print("[DEBUG] Conexión cerrada correctamente")
