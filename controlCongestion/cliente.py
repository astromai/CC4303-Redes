import sys
import SocketTCP

# Configuración
address = ("localhost", 8001)

print("[CLIENTE] Iniciando cliente...")

# Crear cliente
client_socketTCP = SocketTCP.SocketTCP()
print(f"[CLIENTE] Conectando a {address}...")
client_socketTCP.connect(address)
print(f"[CLIENTE] Conectado exitosamente\n")

# Leer de stdin y enviar usando Go Back-N
print("[CLIENTE] Leyendo datos de stdin...")
content = sys.stdin.read()
message = content.encode()
print(f"[CLIENTE] Leídos {len(message)} bytes de stdin\n")

print("[CLIENTE] Enviando datos con Go Back-N + Control de Congestión...")
client_socketTCP.send(message, mode="go_back_n", debug=True, use_cc=True)
print(f"[CLIENTE] Datos enviados exitosamente")
print(f"[CLIENTE] Segmentos enviados: {client_socketTCP.number_of_sent_segments}\n")

# Cerrar conexión
print("[CLIENTE] Cerrando conexión...")
print("[CLIENTE] Enviando FIN al servidor...")
client_socketTCP.close()
print("[CLIENTE] Conexión cerrada\n")
