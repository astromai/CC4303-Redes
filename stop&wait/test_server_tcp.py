from SocketTCP import SocketTCP

# Dirección del servidor
server_address = ('localhost', 8000)

# Crear socket TCP
server = SocketTCP()
server.bind(server_address)
print("Creando SocketTCP - Servidor")

# Aceptar conexión
connection, client_addr = server.accept(loss_probability=20)  # 20% de pérdida simulada
print(f"Conexión aceptada desde {client_addr}")

# Recibir archivo enviado por cliente
received_file = connection.recv(1024)  # Tamaño suficientemente grande
print(f"Archivo recibido ({len(received_file)} bytes):")
print(received_file.decode())

# Test de recv(buff_size) con buff_size < message_length
print("Recibiendo mensaje de prueba en dos partes (buff_size < message_length)...")
part1 = connection.recv(17)
part2 = connection.recv(17)
print(f"Part 1: {part1}")
print(f"Part 2: {part2}")
print(f"Combinado: {part1 + part2}")

# Cierre de conexión
print("Esperando cierre de conexión del cliente...")
connection.recv_close()
print("¡Cierre de conexión exitoso!")
