import socket
import json
from utils.utils import receive_full_message
from utils.helpers import parse_HTTP_message, create_HTTP_message

# Load configuration from JSON file
with open("static/config.json", "r") as file:
    config = json.load(file)
    forbidden_urls = config["blocked"]
    forbidden_words = config["forbidden-words"]

# Load error page
with open("static/error.html", "r") as file:
    error_page = file.read()

# Proxy Server initialization
if __name__ == "__main__":
    buff_size = 4
    end_of_message = "\r\n\r\n"
    proxy_socket_address = ('localhost', 8080)

    print('Creando socket - Servidor Proxy')
    proxy_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    proxy_socket.bind(proxy_socket_address)
    proxy_socket.listen(3)

    while True:
        print('Esperando clientes...')
        # receive message from client
        client_socket, client_socket_address = proxy_socket.accept()
        recv_message_client = receive_full_message(client_socket, buff_size, end_of_message)
        print(f'-> Se ha recibido el siguiente mensaje del cliente: {recv_message_client}')

        # forward message to server
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # parse message to get server address
        http_data = parse_HTTP_message(recv_message_client)
        host = None
        for header in http_data["headers"]:
            if header.lower().startswith("host:"):
                host = header.split(":", 1)[1].strip()
                break
        print(f"-> Host extraído: {host}")
        # check if host is in forbidden list
        start_line = http_data["start_line"]
        print(f"-> Start line: {start_line}")
        uri = start_line.split(" ")[1]
        print(f"-> URI extraída: {uri}")
        if uri in forbidden_urls:
            print(f"-> La URI {uri} está en la lista de prohibidas. Enviando página de error al cliente.")
            response = create_HTTP_message({
                "start_line": "HTTP/1.1 403 Forbidden",
                "headers": [
                    "Content-Type: text/html; charset=UTF-8",
                    f"Content-Length: {len(error_page.encode('utf-8'))}",
                    "Connection: close"
                ],
                "body": error_page
            })
            client_socket.send(response.encode())
            client_socket.close()
            print(f"conexión con {client_socket_address} ha sido cerrada")
            server_socket.close()
            print(f"conexión con {(host, 80)} ha sido cerrada")
            continue

        # if not forbidden, proceed to connect to server
        http_data["headers"].append("X-ElQuePregunta: Tomas")
        method, uri, version = http_data["start_line"].split(" ", 2)
        if uri.startswith("http://"):
            # si la URI absoluta incluye path, lo mantenemos, si no, solo "/"
            parts = uri.split("/", 3)
            if len(parts) > 3:
                uri = "/" + parts[3]
            else:
                uri = "/"
        http_data["start_line"] = f"{method} {uri} {version}"
        http_request_to_server = create_HTTP_message(http_data)
        server_socket_address = (host, 80)
        server_socket.connect(server_socket_address)
        print("-> Conexión establecida con el servidor")
        print("-> Enviando información al servidor")
        print(http_request_to_server)
        server_socket.send(http_request_to_server.encode())

        # receive response from server
        print("-> Esperando respuesta del servidor...")
        recv_message_server = receive_full_message(server_socket, buff_size, end_of_message)
        http_data = parse_HTTP_message(recv_message_server)
        for header in http_data["headers"]:
            if header.lower().startswith("content-type: text/html"):
                body = http_data["body"]
                for word_dict in config["forbidden-words"]:
                    for word, replacement in word_dict.items():
                        body = body.replace(word, replacement)
                http_data["body"] = body
                for i, header in enumerate(http_data["headers"]):
                    if header.lower().startswith("content-length:"):
                        http_data["headers"][i] = f"Content-Length: {len(body.encode('utf-8'))}"
                        break
                break        
        response = create_HTTP_message(http_data)
        print(f'-> Se ha recibido el siguiente mensaje del servidor: {recv_message_server}')
        print("-> Procesando y enviando respuesta al cliente...")
        print(f'-> Se ha enviara el siguiente mensaje al cliente: {response}')
        # forward response to client
        client_socket.send(response.encode())
        print("-> Se ha enviado la respuesta del servidor al cliente")

        server_socket.close()
        print(f"conexión con {server_socket_address} ha sido cerrada")
        client_socket.close()
        print(f"conexión con {client_socket_address} ha sido cerrada")
