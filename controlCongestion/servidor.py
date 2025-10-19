import SocketTCP

# Configuración
address = ("localhost", 8001)

# Crear servidor
server_socketTCP = SocketTCP.SocketTCP()
server_socketTCP.bind(address)

# Aceptar conexión
connection_socketTCP, new_address = server_socketTCP.accept()

# Primer recv para obtener el message_length automáticamente
# y empezar a recibir datos
data = connection_socketTCP.recv(16, mode="go_back_n")
full_content = data

# Seguir recibiendo hasta que message_length y bytes_received coincidan
# (cuando bytes_received >= message_length, recv() resetea las variables)
while connection_socketTCP.message_length > 0:
    data = connection_socketTCP.recv(16, mode="go_back_n")
    full_content += data

# Mostrar contenido recibido
print(full_content.decode())

# Cerrar conexión
connection_socketTCP.recv_close()
