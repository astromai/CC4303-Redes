import socket
import json
import time
from email.utils import formatdate

# Load HTML content from file
with open("index.html", "r") as file:
    html_content = file.read()

# Change for your name 
now = time.time()
http_date = formatdate(timeval=now, localtime=False, usegmt=True)

# Load configuration from JSON file
with open("config.json", "r") as file:
    config = json.load(file)
    name_var = config["name"]


def receive_full_message(connection_socket, buff_size, end_sequence):
    recv_message = connection_socket.recv(buff_size)
    full_message = recv_message
    is_end_of_message = contains_end_of_message(full_message.decode(), end_sequence)

    while not is_end_of_message:
        recv_message = connection_socket.recv(buff_size)
        full_message += recv_message
        is_end_of_message = contains_end_of_message(full_message.decode(), end_sequence)
    
    ''' 
    Debugging message
    print(repr(full_message.decode()))
    print(len(full_message.decode()))
    ''' 

    full_message = remove_end_of_message(full_message.decode(), end_sequence)
    return full_message


def contains_end_of_message(message, end_sequence):
    return message.endswith(end_sequence)


def remove_end_of_message(full_message, end_sequence):
    index = full_message.rfind(end_sequence)
    return full_message[:index]

# parser_HTTP_message: string -> dict[string, List[string]]
# Simple HTTP message parser, returns a dictionary with start line and headers
def parse_HTTP_message(http_message):
    lines = http_message.split("\r\n")
    start_line = lines[0]
    headers = lines[1:]
    headers = [h for h in headers if h]
    return {
        "start_line": start_line,   # string: start line
        "headers": headers          # List[string]: list of headers
    }

# create_HTTP_message: dict -> string
# Simple HTTP message creator from a dictionary
def create_HTTP_message(http_dataStruct):
    message = http_dataStruct["start_line"]+"\r\n"
    for header in http_dataStruct["headers"]:
        message += header + "\r\n"
    message += "\r\n"
    return message

# create_HTTP_response: string -> string
def create_HTTP_response(html_body):
    start_line = f"HTTP/1.1 200 OK\r\n"
    headers = [
        "Server: Simple-Python-HTTP-Server\r\n",
        f"Date: {http_date}\r\n",
        f"Content-Length: {len(html_body.encode('utf-8'))}\r\n",
        "Content-Type: text/html; charset=UTF-8\r\n",
        "Connection: keep-alive\r\n",
        f"X-ElQuePregunta: {name_var}\r\n",
    ]
    return f"{start_line}{''.join(headers)}\r\n{html_body}"

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
        html_final = html_content.replace("{{name}}", name_var)
        http_response = create_HTTP_response(html_final)
        new_socket.send(http_response.encode())
        new_socket.close()
        print(f"conexión con {new_socket_address} ha sido cerrada")
