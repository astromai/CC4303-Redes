import socket
import json
from utils.helpers import create_HTTP_response
from utils.utils import receive_full_message

# Load HTML content from file
with open("static/index.html", "r") as file:
    html_content = file.read()

# Load configuration from JSON file
with open("static/config.json", "r") as file:
    config = json.load(file)
    name = config["name"]

# Server initialization
if __name__ == "__main__":
    buff_size = 4
    end_of_message = "\r\n\r\n"
    new_socket_address = ('localhost', 8000)

    print('Creando socket - Servidor')
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(new_socket_address)
    server_socket.listen(3)
    print('... Esperando clientes')
    while True:
        new_socket, new_socket_address = server_socket.accept()
        recv_message = receive_full_message(new_socket, buff_size, end_of_message)
        print(f' -> Se ha recibido el siguiente mensaje: {recv_message}')
        response_message = f"Se ha sido recibido con éxito el mensaje: {recv_message}"
        http_response = create_HTTP_response(html_content, name)
        new_socket.send(http_response.encode())
        new_socket.close()
        print(f"conexión con {new_socket_address} ha sido cerrada")
