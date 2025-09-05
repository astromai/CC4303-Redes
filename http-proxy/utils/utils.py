def receive_full_message(connection_socket, buff_size, end_sequence):
    recv_message = connection_socket.recv(buff_size)
    full_message = recv_message
    while not contains_end_of_message(full_message.decode(), end_sequence):
        recv_message = connection_socket.recv(buff_size)
        if not recv_message:
            break
        full_message += recv_message

    full_message_decoded = full_message.decode()
    header_part, _, body_part = full_message_decoded.partition(end_sequence)
    
    content_length = 0
    for line in header_part.split("\r\n"):
        if line.lower().startswith("content-length:"):
            content_length = int(line.split(":", 1)[1].strip())
            break

    if content_length > 0:
        body_bytes = body_part.encode()
        while len(body_bytes) < content_length:
            part = connection_socket.recv(buff_size)
            if not part:
                break
            body_bytes += part
        final_message = header_part + end_sequence + body_bytes.decode()
    else:
        final_message = header_part + end_sequence
        
    return final_message


def contains_end_of_message(message, end_sequence):
    return message.endswith(end_sequence)

def remove_end_of_message(full_message, end_sequence):
    index = full_message.rfind(end_sequence)
    return full_message[:index]
