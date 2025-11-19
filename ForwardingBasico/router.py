import sys
import socket

# Paso 2
if len(sys.argv) != 4:
    print("Uso: python3 router.py <IP> <puerto> <archivo_rutas>")
    sys.exit(1)

router_IP = sys.argv[1]
router_puerto = int(sys.argv[2])
router_rutas = sys.argv[3]

# Imprimir para verificar (test del paso 2)
print(f"Router iniciado en {router_IP}:{router_puerto}")
print(f"Tabla de rutas: {router_rutas}")

# Paso 4
def parse_packet(IP_packet):
    # Decodificar el paquete
    packet_str = IP_packet.decode()
    
    # Separar por punto y coma
    parts = packet_str.split(';')
    
    parsed_packet = {
        'ip': parts[0],
        'puerto': int(parts[1]),
        'mensaje': parts[2]
    }
    
    return parsed_packet

# Paso 4
def create_packet(parsed_IP_packet):
    packet_str = f"{parsed_IP_packet['ip']};{parsed_IP_packet['puerto']};{parsed_IP_packet['mensaje']}"
    return packet_str

# Diccionario global para llevar la cuenta de round-robin
# Estructura: {(ip_red, puerto_inicial, puerto_final): índice_actual}
round_robin_counter = {}

# Paso 5 y 8 (modificado para round-robin)
def check_routes(routes_file_name, destination_address):
    dest_ip, dest_puerto = destination_address
    
    # Buscar todas las rutas que coinciden
    matching_routes = []
    
    with open(routes_file_name, 'r') as file:
        for line in file:
            line = line.strip()
            parts = line.split()
            
            network_ip = parts[0]
            puerto_inicial = int(parts[1])
            puerto_final = int(parts[2])
            next_hop_ip = parts[3]
            next_hop_puerto = int(parts[4])
            
            # Verificar si coincide
            if dest_ip == network_ip and puerto_inicial <= dest_puerto <= puerto_final:
                matching_routes.append((next_hop_ip, next_hop_puerto))
    
    # Si no hay rutas
    if len(matching_routes) == 0:
        return None
    
    # Si hay una sola ruta
    if len(matching_routes) == 1:
        return matching_routes[0]
    
    # Si hay múltiples rutas, usar round-robin
    # Usar puerto_destino como clave para mantener el estado
    if dest_puerto not in round_robin_counter:
        round_robin_counter[dest_puerto] = 0
    
    # Seleccionar la ruta actual
    index = round_robin_counter[dest_puerto]
    selected_route = matching_routes[index]
    
    # Actualizar el contador para la próxima vez
    round_robin_counter[dest_puerto] = (index + 1) % len(matching_routes)
    
    return selected_route

# Crear socket UDP
buff_size = 1024
server_address = (router_IP, router_puerto)

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(server_address)
print(f"Router escuchando en {router_IP}:{router_puerto}")

# Test de funciones parse_packet y create_packet
print("\n--- Test de parse_packet y create_packet ---")
IP_packet_v1 = "127.0.0.1;8881;hola".encode()
parsed_IP_packet = parse_packet(IP_packet_v1)
print(f"Paquete parseado: {parsed_IP_packet}")
IP_packet_v2_str = create_packet(parsed_IP_packet)
print(f"Paquete recreado: {IP_packet_v2_str}")
IP_packet_v2 = IP_packet_v2_str.encode()
print("IP_packet_v1 == IP_packet_v2 ? {}".format(IP_packet_v1 == IP_packet_v2))
print("--- Fin del test ---\n")

# Test de función check_routes
print("--- Test de check_routes ---")
# Test con rutas del ejemplo 2 (R1)
print("Probando con rutas_R1_v2.txt:")
result = check_routes('rutas_R1_v2.txt', ('127.0.0.1', 8882))
print(f"  Destino (127.0.0.1, 8882): {result}")
result = check_routes('rutas_R1_v2.txt', ('127.0.0.1', 8883))
print(f"  Destino (127.0.0.1, 8883): {result}")
result = check_routes('rutas_R1_v2.txt', ('127.0.0.1', 8884))
print(f"  Destino (127.0.0.1, 8884) [fuera de red]: {result}")
print("--- Fin del test ---\n")

while True:
    data, address = sock.recvfrom(buff_size)
    
    # Paso 6
    # Parsear el paquete
    parsed_packet = parse_packet(data)
    dest_ip = parsed_packet['ip']
    dest_puerto = parsed_packet['puerto']
    mensaje = parsed_packet['mensaje']
    
    destination_address = (dest_ip, dest_puerto)
    paquete_ip = f"{dest_ip};{dest_puerto};{mensaje}"
    
    # Verificar si el paquete es para este router
    if dest_ip == router_IP and dest_puerto == router_puerto:
        # Imprimir solo el mensaje (sin headers)
        print(mensaje)
    else:
        # El paquete no es para este router, consultar rutas
        next_hop = check_routes(router_rutas, destination_address)
        
        if next_hop is None:
            # No hay ruta
            print(f"No hay rutas hacia {destination_address} para paquete {paquete_ip}")
        else:
            # Hay ruta, hacer forward
            next_hop_ip, next_hop_puerto = next_hop
            print(f"Redirigiendo paquete {paquete_ip} con destino final {destination_address} desde {(router_IP, router_puerto)} hacia {(next_hop_ip, next_hop_puerto)}")
            
            # Enviar el paquete
            packet_to_send = create_packet(parsed_packet).encode()
            sock.sendto(packet_to_send, (next_hop_ip, next_hop_puerto))