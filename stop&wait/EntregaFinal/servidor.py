import sys
import SocketTCP

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Uso: python3 servidor.py <puerto>")
        sys.exit(1)

    port = int(sys.argv[1])
    server_address = ('localhost', port)

    # Crear socket servidor
    server_socket = SocketTCP.SocketTCP()
    server_socket.bind(server_address)

    print(f"[DEBUG] Servidor escuchando en localhost:{port}")

    # Aceptar conexión
    connection_socket, client_address = server_socket.accept()
    print(f"[DEBUG] Cliente conectado desde {client_address}")

    # Recibir datos
    received_data = b""
    chunk_size = 1024

    while True:
        chunk = connection_socket.recv(chunk_size)
        if not chunk:
            break
        received_data += chunk
        print(f"[DEBUG] Recibidos {len(chunk)} bytes (total: {len(received_data)})")
        
        # Si recibimos menos del chunk_size, asumimos que terminó
        if len(chunk) < chunk_size:
            break

    print(f"[DEBUG] Recepción completa: {len(received_data)} bytes totales")

    # Mostrar el contenido recibido
    print("--- CONTENIDO RECIBIDO ---")
    print(received_data.decode())
    print("--- FIN DEL CONTENIDO ---")

    # Esperar cierre del cliente
    print("[DEBUG] Esperando cierre de conexión del cliente...")
    connection_socket.recv_close()
    print("[DEBUG] Conexión cerrada")
