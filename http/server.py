import socket

def receive_full_message(connection_socket, buff_size, end_sequence):

    recv_message = connection_socket.recv(buff_size)
    full_message = recv_message
    is_end_of_message = contains_end_of_message(full_message.decode(), end_sequence)

    while not is_end_of_message:
        recv_message = connection_socket.recv(buff_size)
        full_message += recv_message
        is_end_of_message = contains_end_of_message(full_message.decode(), end_sequence)

    full_message = remove_end_of_message(full_message.decode(), end_sequence)
    return full_message


def contains_end_of_message(message, end_sequence):
    return message.endswith(end_sequence)


def remove_end_of_message(full_message, end_sequence):
    index = full_message.rfind(end_sequence)
    return full_message[:index]

if __name__ == "__main__":
    buff_size = 4
    end_of_message = "\n"
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
        new_socket.send(response_message.encode())
        new_socket.close()
        print(f"conexión con {new_socket_address} ha sido cerrada")
