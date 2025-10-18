import sys
from SocketTCP import SocketTCP

# Lectura de archivo desde stdin
message = sys.stdin.read().encode()

# Dirección del servidor
server_address = ('localhost', 8000)

# Crear socket TCP
client = SocketTCP()
print("Creando SocketTCP - Cliente")
client.connect(server_address, loss_probability=20)  # 20% de pérdida simulada

print(f"Enviando archivo ({len(message)} bytes) al servidor...")

# Enviar mensaje completo con Stop & Wait
client.send(message)

print("Archivo enviado completamente.")

# Test de recv(buff_size) con buff_size < message_length
# Enviar mensaje de prueba dividido en dos
test_message = b"A" * 34  # 2*n bytes, n=17
client.send(test_message)

print("Enviando mensaje de prueba de 34 bytes dividido en recv de 17...")
received_part_1 = client.recv(17)
received_part_2 = client.recv(17)
print(f"Mensaje recibido dividido: {received_part_1} | {received_part_2}")
print(f"Mensaje combinado: {received_part_1 + received_part_2}")

# Cierre de conexión
print("Cerrando conexión...")
client.close()
print("¡Cierre de conexión exitoso!")
