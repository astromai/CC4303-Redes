import socket
from utils.helpers import create_HTTP_response, parse_HTTP_message
from utils.utils import receive_full_message

# Load HTML content from file
with open("static/index.html", "r") as file:
    html_content = file.read()

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
        name = parse_HTTP_message(recv_message)["headers"].get("X-ElQuePregunta", name)
        for header in parse_HTTP_message(recv_message)["headers"]:
            if header.lower().startswith("x-elquepregunta:"):
                name = header.split(":", 1)[1].strip()
                break
        http_response = create_HTTP_response(html_content, name)
        new_socket.send(http_response.encode())
        new_socket.close()
        print(f"conexión con {new_socket_address} ha sido cerrada")
