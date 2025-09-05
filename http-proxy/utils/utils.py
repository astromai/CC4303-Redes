def receive_full_message(connection_socket, buff_size, end_sequence="\r\n\r\n"):
    # Leer datos hasta que aparezca el end_sequence
    recv_message = connection_socket.recv(buff_size)
    full_message = recv_message
    while not contains_end_of_message(full_message.decode(), end_sequence):
        recv_message = connection_socket.recv(buff_size)
        full_message += recv_message

    # Separar headers y body inicial
    full_message_decoded = full_message.decode()
    header_part, _, body_part = full_message_decoded.partition(end_sequence)
    
    # Revisar Content-Length en headers
    content_length = 0
    for line in header_part.split("\r\n"):
        if line.lower().startswith("content-length:"):
            content_length = int(line.split(":", 1)[1].strip())
            break

    # Leer body restante si existe
    body_bytes = body_part.encode()
    while len(body_bytes) < content_length:
        body_bytes += connection_socket.recv(buff_size)

    # Combinar headers y body para devolver
    final_message = header_part + end_sequence + body_bytes.decode()
    return final_message


def contains_end_of_message(message, end_sequence):
    return message.endswith(end_sequence)

def remove_end_of_message(full_message, end_sequence):
    index = full_message.rfind(end_sequence)
    return full_message[:index]
