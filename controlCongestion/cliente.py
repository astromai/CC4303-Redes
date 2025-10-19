import sys
import SocketTCP

# Configuración
address = ("localhost", 8001)

# Crear cliente
client_socketTCP = SocketTCP.SocketTCP()
client_socketTCP.connect(address)

# Leer de stdin y enviar usando Go Back-N
content = sys.stdin.read()
message = content.encode()

client_socketTCP.send(message, mode="go_back_n")

# Cerrar conexión
client_socketTCP.close()
