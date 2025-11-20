# router.py
# Versión fusionada: base actividad 1 (formato ; ) + fragmentación (MTU)
# Uso: python3 router.py <IP> <puerto> <archivo_rutas>
# Cambios importantes están marcados con comentarios "# CAMBIO:" o "# FIX:" en las funciones.

import sys
import socket
import os

# -------------------- parámetros y checks iniciales --------------------
if len(sys.argv) != 4:
    print("Uso: python3 router.py <IP> <puerto> <archivo_rutas>")
    sys.exit(1)

router_IP = sys.argv[1]
router_puerto = int(sys.argv[2])
router_rutas = sys.argv[3]

print(f"Router iniciado en {router_IP}:{router_puerto}")
print(f"Tabla de rutas: {router_rutas}")

# -------------------- utilitarios de formateo (padding) --------------------
def pad_n(num, n):
    """Devuelve str(num) con ceros a la izquierda hasta largo n."""
    s = str(int(num))  # asegurar int -> str limpio
    return s.zfill(n)

def pad_port(p):
    return pad_n(p, 4)

def pad_ttl(t):
    return pad_n(t, 3)

def pad_8(n):
    return pad_n(n, 8)

# -------------------- PARSE / CREATE (FORMATO con ; ) --------------------
# CAMBIO: parse_packet ahora soporta el formato de la actividad 1 ampliado con campos de fragmentación.
#        Acepta input bytes o str. Retorna dict con tipos correctos (TAMANO, OFFSET, ID, TTL como int).
def parse_packet(IP_packet):
    # Acepta bytes o str
    packet_str = IP_packet.decode() if isinstance(IP_packet, bytes) else IP_packet
    # Separador de la actividad 1: ';'
    parts = packet_str.split(';')
    # Soportamos dos formatos:
    # - formato simple anterior (3 campos): ip;puerto;mensaje
    # - formato fragmentación (8 campos): ip;puerto;TTL;ID;OFFSET;TAMANO;FLAG;mensaje
    if len(parts) == 3:
        return {
            'IP': parts[0],
            'PUERTO': int(parts[1]),
            'TTL': None,
            'ID': None,
            'OFFSET': None,
            'TAMANO': None,
            'FLAG': None,
            'MENSAJE': parts[2]
        }
    elif len(parts) >= 8:
        # Si el mensaje contiene ';' adicionales, juntarlos (partes[7:])
        mensaje = ';'.join(parts[7:])
        return {
            'IP': parts[0],
            'PUERTO': int(parts[1]),
            'TTL': int(parts[2]),
            'ID': int(parts[3]),
            'OFFSET': int(parts[4]),
            'TAMANO': int(parts[5]),
            'FLAG': int(parts[6]),
            'MENSAJE': mensaje
        }
    else:
        raise ValueError("Paquete con formato desconocido: " + packet_str)

# CAMBIO: create_packet crea siempre la representación con ';' y padding
#         Los campos TTL(3), PUERTO(4), ID/OFFSET/TAMANO(8) se formatean según enunciado.
def create_packet(parsed_IP_packet):
    # parsed_IP_packet es dict con campos (IP, PUERTO, TTL, ID, OFFSET, TAMANO, FLAG, MENSAJE)
    ip = parsed_IP_packet['IP']
    puerto = pad_port(parsed_IP_packet['PUERTO'])
    ttl = pad_ttl(parsed_IP_packet['TTL'])
    id_str = pad_8(parsed_IP_packet['ID'])
    offset_str = pad_8(parsed_IP_packet['OFFSET'])
    tamano_str = pad_8(parsed_IP_packet['TAMANO'])
    flag_str = str(int(parsed_IP_packet['FLAG']))  # 1 dígito
    mensaje = parsed_IP_packet['MENSAJE']
    packet_str = f"{ip};{puerto};{ttl};{id_str};{offset_str};{tamano_str};{flag_str};{mensaje}"
    return packet_str.encode()

# -------------------- CHECK_ROUTES (devuelve next_hop y MTU) --------------------
# CAMBIO: ahora parsea tablas con 6 columnas: red puerto_inicial puerto_final ip_next puerto_next mtu
#        implementa round-robin por puerto_destino manteniendo una cache 'rutas_cache' similar a la idea de la base.
rutas_cache = {}   # key: puerto_destino -> lista de (next_ip,next_puerto,mtu)
rr_index = {}      # key: puerto_destino -> current index

def check_routes(routes_file_name, destination_address):
    dest_ip, dest_puerto = destination_address

    # Si ya tenemos rutas en cache para ese puerto destino, usamos round-robin sobre esa lista
    if dest_puerto in rutas_cache and len(rutas_cache[dest_puerto]) > 0:
        idx = rr_index.get(dest_puerto, 0)
        sel = rutas_cache[dest_puerto][idx]
        rr_index[dest_puerto] = (idx + 1) % len(rutas_cache[dest_puerto])
        return ((sel[0], sel[1]), sel[2])

    # Sino, leemos el archivo de rutas (soportando archivos rutas_RX_v3_mtu.txt)
    matching = []
    try:
        with open(routes_file_name, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                parts = line.split()
                # formato esperado: network_ip puerto_inicial puerto_final next_hop_ip next_hop_puerto mtu
                if len(parts) >= 6:
                    network_ip = parts[0]
                    puerto_inicial = int(parts[1])
                    puerto_final = int(parts[2])
                    next_hop_ip = parts[3]
                    next_hop_puerto = int(parts[4])
                    mtu = int(parts[5])
                    if dest_ip == network_ip and puerto_inicial <= dest_puerto <= puerto_final:
                        matching.append((next_hop_ip, next_hop_puerto, mtu))
    except FileNotFoundError:
        print(f"Error: El archivo de rutas '{routes_file_name}' no se encontró.")
        return None
    except Exception as e:
        print(f"Error al leer las rutas: {e}")
        return None

    if len(matching) == 0:
        return None

    # Guardar en cache para round-robin
    rutas_cache[dest_puerto] = matching
    rr_index[dest_puerto] = 0
    sel = matching[0]
    rr_index[dest_puerto] = 1 % len(matching)
    return ((sel[0], sel[1]), sel[2])

# -------------------- FRAGMENTACIÓN --------------------
# CAMBIO: fragment_IP_packet ahora usa el formato de packet (;) y calcula header_len como
#        len(packet) - len(mensaje_bytes) (robusto para fragmentos ya existentes).
#        Devuelve lista de bytes (cada fragment es create_packet(...))
def fragment_IP_packet(IP_packet_bytes, MTU):
    # Si ya cabe, retornar lista de un elemento
    if len(IP_packet_bytes) <= MTU:
        return [IP_packet_bytes]

    # Parsear el paquete
    pkt = parse_packet(IP_packet_bytes)
    
    # Calcular tamaño del header de forma FIJA según el formato
    # IP(9) + ;(1) + PUERTO(4) + ;(1) + TTL(3) + ;(1) + ID(8) + ;(1) + OFFSET(8) + ;(1) + TAMANO(8) + ;(1) + FLAG(1) + ;(1) = 48 bytes
    header_len = 48
    
    # Verificar que el MTU sea suficiente para el header
    if MTU <= header_len:
        return [IP_packet_bytes]

    payload_max = MTU - header_len
    mensaje_bytes = pkt['MENSAJE'].encode()
    offset = pkt['OFFSET']
    fragments = []

    # Fragmentar el mensaje
    start = 0
    while start < len(mensaje_bytes):
        end = start + payload_max
        parte_bytes = mensaje_bytes[start:end]
        parte_str = parte_bytes.decode('latin-1')  # Usar latin-1 para preservar todos los bytes
        
        # Determinar FLAG: 1 si hay más fragmentos, 0 si es el último
        flag = 1 if end < len(mensaje_bytes) else 0
        
        nuevo_pkt = {
            'IP': pkt['IP'],
            'PUERTO': pkt['PUERTO'],
            'TTL': pkt['TTL'],
            'ID': pkt['ID'],
            'OFFSET': offset + start,
            'TAMANO': len(parte_bytes),
            'FLAG': flag,
            'MENSAJE': parte_str
        }
        
        fragment_bytes = create_packet(nuevo_pkt)
        fragments.append(fragment_bytes)
        start = end

    return fragments

# -------------------- REENSAMBLAJE --------------------
# CAMBIO: reassemble_IP_packet espera una lista de BYTES (fragmentos), los parsea correctamente,
#        valida offsets contiguos, valida que todos menos el último tengan FLAG=1 y retorna dict si OK.
def reassemble_IP_packet(fragment_list):
    if not fragment_list:
        return None

    # parse fragments -> dicts
    frags = [parse_packet(f) for f in fragment_list]

    # ordenar por OFFSET
    frags.sort(key=lambda x: x['OFFSET'])

    # si hay un solo fragmento -> puede ser paquete completo o fragmento incompleto
    if len(frags) == 1:
        single = frags[0]
        # si OFFSET == 0 y FLAG == 0 => paquete completo
        if single['OFFSET'] == 0 and single['FLAG'] == 0:
            return single
        else:
            return None

    # validar que todos menos el ultimo tengan FLAG==1 y el ultimo FLAG==0
    for i in range(len(frags)-1):
        if frags[i]['FLAG'] != 1:
            return None
    if frags[-1]['FLAG'] != 0:
        return None

    # reconstruir mensaje verificando offsets contiguos
    expected_offset = frags[0]['OFFSET']  # normalmente 0, pero soportamos offsets iniciales
    mensaje_parts = []
    total_payload = 0
    for f in frags:
        if f['OFFSET'] != expected_offset:
            return None
        mensaje_parts.append(f['MENSAJE'])
        expected_offset += f['TAMANO']
        total_payload += f['TAMANO']

    mensaje = ''.join(mensaje_parts)

    return {
        'IP': frags[0]['IP'],
        'PUERTO': frags[0]['PUERTO'],
        'TTL': frags[0]['TTL'],
        'ID': frags[0]['ID'],
        'OFFSET': 0,
        'TAMANO': total_payload,
        'FLAG': 0,
        'MENSAJE': mensaje
    }

# -------------------- LOOP PRINCIPAL (socket) --------------------
buff_size = 4096
server_address = (router_IP, router_puerto)

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(server_address)
print(f"Router escuchando en {router_IP}:{router_puerto}")

# diccionario para almacenar fragmentos por ID
# key: ID (int) -> list de bytes (fragmentos recibidos, en orden de llegada)
fragment_buffer = {}

# --- Tests (simples) para parse/create y check_routes (del base) ---
print("\n--- Test parse/create (formato fragmentación) ---")
IP_packet_v1 = "127.0.0.1;8881;010;00000001;00000000;00000005;0;hola".encode()
parsed = parse_packet(IP_packet_v1)
print("Parsed:", parsed)
recreated = create_packet(parsed)
print("Recreated bytes:", recreated)
print("--- Fin test ---\n")

print("--- Test check_routes ---")
# Intenta cargar el archivo de rutas que mencionaste (rutas_R1_v3_mtu.txt etc.)
if os.path.exists(router_rutas):
    test_res = check_routes(router_rutas, ('127.0.0.1', 8882))
    print("check_routes test:", test_res)
else:
    print(f"Archivo de rutas {router_rutas} no encontrado para test.")
print("--- Fin test rutas ---\n")

# Bucle principal
while True:
    data, address = sock.recvfrom(buff_size)  # data = bytes
    try:
        MSG = parse_packet(data)
    except Exception as e:
        print("Error parseando paquete recibido:", e)
        continue

    # TTL check: si TTL == 0 => descartar
    if MSG['TTL'] is not None and MSG['TTL'] == 0:
        print(f"Se recibió paquete {data} con TTL 0")
        continue

    # Si el paquete es para este router -> almacenar para reensamblaje o imprimir
    if MSG['IP'] == router_IP and MSG['PUERTO'] == router_puerto:
        # Guardar fragmento (bytes) por ID
        pkt_id = MSG['ID']
        if pkt_id is None:
            # paquete sin headers de fragmentación, imprimir mensaje directo
            print(MSG['MENSAJE'])
            continue

        if pkt_id not in fragment_buffer:
            fragment_buffer[pkt_id] = []
        # Guardar los bytes tal cual llegaron
        fragment_buffer[pkt_id].append(data)

        # Intento de reensamblaje
        rearmado = reassemble_IP_packet(fragment_buffer[pkt_id])
        if rearmado is not None:
            # paquete reensamblado correctamente
            del fragment_buffer[pkt_id]
            print(rearmado['MENSAJE'])
        else:
            # aún faltan fragmentos
            pass
    else:
        # Forwarding: obtener next hop y MTU
        tupla = check_routes(router_rutas, (MSG['IP'], MSG['PUERTO']))
        if tupla is None:
            paquete_ip = f"{MSG['IP']};{MSG['PUERTO']};{MSG['MENSAJE']}"
            print(f"No hay rutas hacia {(MSG['IP'],MSG['PUERTO'])} para paquete {paquete_ip}")
            continue

        direccion, mtu = tupla
        next_ip, next_port = direccion

        # Reducir TTL ANTES de enviar
        if MSG['TTL'] is not None:
            MSG['TTL'] -= 1
            if MSG['TTL'] < 0:
                print(f"TTL expirado para paquete {data}")
                continue

        # Reconstruir paquete bytes (con create_packet) y fragmentar según MTU
        mensaje_bytes_original = MSG['MENSAJE'].encode()
        # Reconstruir paquete completo en bytes para pasar a fragment_IP_packet
        pkt_full = create_packet({
            'IP': MSG['IP'],
            'PUERTO': MSG['PUERTO'],
            'TTL': MSG['TTL'],
            'ID': MSG['ID'],
            'OFFSET': MSG['OFFSET'],
            'TAMANO': MSG['TAMANO'] if MSG['TAMANO'] is not None else len(mensaje_bytes_original),
            'FLAG': MSG['FLAG'] if MSG['FLAG'] is not None else 0,
            'MENSAJE': MSG['MENSAJE']
        })

        # Fragmentar usando MTU
        fragments = fragment_IP_packet(pkt_full, mtu)
        # Enviar cada fragmento (ya son bytes)
        for frag in fragments:
            print(f"redirigiendo paquete {frag} con destino final {(MSG['IP'],MSG['PUERTO'])} desde {(router_IP,router_puerto)} hacia {(next_ip,next_port)}")
            sock.sendto(frag, (next_ip, next_port))
