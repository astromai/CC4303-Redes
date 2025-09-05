import socket
import json
from utils.utils import receive_full_message
from utils.helpers import parse_HTTP_message

# Load configuration from JSON file
with open("static/config.json", "r") as file:
    config = json.load(file)
    name_var = config["name"]

# Proxy Server initialization
if __name__ == "__main__":
    buff_size = 4
    end_of_message = "\r\n\r\n"
    proxy_socket_address = ('localhost', 8080)

    print('Creando socket - Servidor Proxy')
    proxy_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    proxy_socket.bind(proxy_socket_address)
    proxy_socket.listen(3)
    print('... Esperando clientes')

    while True:
        # receive message from client
        client_socket, client_socket_address = proxy_socket.accept()
        recv_message_client = receive_full_message(client_socket, buff_size, end_of_message)
        print(f' -> Se ha recibido el siguiente mensaje del cliente: {recv_message_client}')

        # forward message to server
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # parse message to get server address
        http_data = parse_HTTP_message(recv_message_client)
        host = None
        for header in http_data["headers"]:
            if header.lower().startswith("host:"):
                host = header.split(":", 1)[1].strip()
                break
        server_socket_address = (host, 80)
        server_socket.connect(server_socket_address)
        print("-> Conexión establecida con el servidor")
        print("-> Enviando información al servidor")
        server_socket.send(recv_message_client.encode())

        # receive response from server
        print("-> Esperando respuesta del servidor...")
        recv_message_server = receive_full_message(server_socket, buff_size, end_of_message)
        print(f' -> Se ha recibido el siguiente mensaje del servidor: {recv_message_server}')

        # forward response to client
        client_socket.send(recv_message_server.encode())
        print("-> Se ha enviado la respuesta del servidor al cliente")

        server_socket.close()
        print(f"conexión con {server_socket_address} ha sido cerrada")
        client_socket.close()
        print(f"conexión con {client_socket_address} ha sido cerrada")
