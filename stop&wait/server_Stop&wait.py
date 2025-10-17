import socket
# Importamos las funciones de utils para recepción por trozos
from utils import receive_full_mesage, end_of_message

if __name__ == "__main__":
    # Usamos el mismo tamaño de buffer que está definido en utils
    buff_size = 16  # Tamaño máximo de paquete
    server_address = ('localhost', 8000)

    print('Creando socket - Servidor')
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind(server_address)

    print('... Esperando clientes en puerto 8000')

    while True:
        # Recibimos el mensaje completo usando receive_full_mesage
        received_message, client_address = receive_full_mesage(server_socket, buff_size, end_of_message)
        
        print(f"-> Archivo recibido desde {client_address}")
        print(f"-> Tamaño: {len(received_message)} bytes")
        
        # Imprimimos el contenido del archivo en salida estándar
        print("--- CONTENIDO DEL ARCHIVO ---")
        print(received_message.decode())
        print("--- FIN DEL ARCHIVO ---")
        
        print("Esperando siguiente cliente...\n")
