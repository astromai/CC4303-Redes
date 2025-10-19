import socket
import random
import time
from slidingWindow import slidingWindowCC
from socketudp import socketUDP


class CongestionControl:
    def __init__(self, window_size=4, timeout=2):
        # socket UDP interno para manejo de timers
        self.udp_helper = socketUDP()
        self.sock = self.udp_helper.socket_udp
        self.destino = (None, None)
        self.origen = (None, None)
        self.num_seq = 0
        self.timeout = timeout  # Segundos por timer
        self.conectado = False
        self.buffer_size = 16  # Tamaño máximo de paquete
        self.message_length = 0
        self.bytes_received = 0
        self.receive_buffer = b""
        self.window_size = window_size
        self.sliding_window = None  # Se inicializa en send()

    @staticmethod
    def create_segment(syn=0, ack=0, fin=0, seq=0, data=bytes()):
        header = f"{syn}|||{ack}|||{fin}|||{seq}|||"
        return header.encode() + data

    @staticmethod
    def parse_segment(segment_bytes):
        segment_str = segment_bytes.decode()
        parts = segment_str.split("|||", 4)
        if len(parts) < 4:
            return None
        syn, ack, fin, seq = map(int, parts[:4])
        data = parts[4].encode() if len(parts) > 4 else bytes()
        return {"syn": syn, "ack": ack, "fin": fin, "seq": seq, "data": data}

    def bind(self, address):
        self.origen = address
        self.sock.bind(address)

    def connect(self, address):
        self.destino = address
        self.num_seq = random.randint(0, 100)
        syn_segment = self.create_segment(syn=1, seq=self.num_seq)
        while True:
            self.sock.sendto(syn_segment, self.destino)
            self.sock.settimeout(self.timeout)
            try:
                response, server_address = self.sock.recvfrom(1024)
                parsed_response = self.parse_segment(response)
                if parsed_response and parsed_response["syn"] == 1 and parsed_response["ack"] == 1:
                    self.num_seq += 1
                    ack_segment = self.create_segment(ack=1, seq=self.num_seq)
                    self.sock.sendto(ack_segment, server_address)
                    self.destino = server_address
                    self.conectado = True
                    break
            except socket.timeout:
                continue

    def accept(self):
        data, client_address = self.sock.recvfrom(1024)
        parsed_data = self.parse_segment(data)
        if parsed_data and parsed_data["syn"] == 1:
            new_socket = SocketTCP(self.window_size, self.timeout)
            new_socket.destino = client_address
            new_socket.origen = (self.origen[0], self.origen[1] + 1)
            new_socket.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            new_socket.sock.bind(new_socket.origen)
            new_socket.num_seq = random.randint(0, 100)
            syn_ack = new_socket.create_segment(syn=1, ack=1, seq=new_socket.num_seq)
            while True:
                new_socket.sock.sendto(syn_ack, client_address)
                new_socket.sock.settimeout(new_socket.timeout)
                try:
                    ack_data, _ = new_socket.sock.recvfrom(1024)
                    ack_parsed = self.parse_segment(ack_data)
                    if ack_parsed and ack_parsed["ack"] == 1:
                        new_socket.conectado = True
                        new_socket.num_seq += 1
                        return new_socket, new_socket.origen
                except socket.timeout:
                    continue
        return None, None

    def send_con_perdidas_tcp(self, segment, loss_probability=0):
        if random.randint(0, 100) >= loss_probability:
            self.sock.sendto(segment, self.destino)
        else:
            print(f"Se perdió segmento: {segment[:20]}...")

    def recv_con_perdidas_tcp(self, loss_probability=0):
        while True:
            buffer, address = self.sock.recvfrom(1024)
            if random.randint(0, 100) > loss_probability:
                return buffer, address

    def send(self, message):
        if not self.conectado:
            return

        # Preparar segmentos de 16 bytes
        segments = []
        seq = self.num_seq
        for i in range(0, len(message), self.buffer_size):
            data_slice = message[i:i+self.buffer_size]
            segments.append(self.create_segment(seq=seq, data=data_slice))
            seq += len(data_slice)

        # Crear ventana deslizante
        self.sliding_window = SlidingWindowCC(self.window_size, segments, self.num_seq)
        self.num_seq = seq

        # Inicializar timers
        self.udp_helper.settimeout(self.timeout)
        self.udp_helper.set_timer_list_length(self.window_size)

        base = 0  # Índice del primer segmento en ventana
        next_seg = 0  # Índice del siguiente segmento a enviar

        while base < len(segments):
            # Enviar todos los segmentos que aún no se enviaron dentro de la ventana
            for i in range(next_seg, min(base + self.window_size, len(segments))):
                seg_data = self.sliding_window.get_data(i - base)
                self.udp_helper.sendto(seg_data, self.destino, timer_index=i - base)
            next_seg = base + self.window_size

            # Esperar ACKs o timeout
            try:
                ack_data, _ = self.udp_helper.recvfrom(1024)
                ack_parsed = self.parse_segment(ack_data)
                if ack_parsed and ack_parsed["ack"] == 1:
                    # Mover ventana
                    steps = 0
                    for j in range(self.window_size):
                        if self.sliding_window.get_sequence_number(j) < ack_parsed["seq"]:
                            steps += 1
                            self.udp_helper.stop_timer(j)
                    self.sliding_window.move_window(steps)
                    base += steps
            except TimeoutError as e:
                # Retransmitir segmentos de la ventana que expiraron
                for t_index in self.udp_helper.get_stopped_timers():
                    seg_data = self.sliding_window.get_data(t_index)
                    if seg_data is not None:
                        print(f"Retransmitiendo segmento con seq {self.sliding_window.get_sequence_number(t_index)}")
                        self.udp_helper.sendto(seg_data, self.destino, timer_index=t_index)

    def recv(self, buff_size):
        if not self.conectado:
            return b""
        if self.bytes_received == 0 and self.message_length == 0:
            self.receive_buffer = b""
            while True:
                data, _ = self.recv_con_perdidas_tcp()
                length_parsed = self.parse_segment(data)
                if length_parsed and length_parsed["data"]:
                    ack_segment = self.create_segment(ack=1, seq=length_parsed["seq"] + 1)
                    self.send_con_perdidas_tcp(ack_segment)
                    self.message_length = int(length_parsed["data"].decode())
                    break

        bytes_to_receive = min(buff_size, self.message_length - self.bytes_received)
        while len(self.receive_buffer) < bytes_to_receive:
            data, _ = self.recv_con_perdidas_tcp()
            parsed = self.parse_segment(data)
            if parsed and parsed["data"]:
                ack_segment = self.create_segment(ack=1, seq=parsed["seq"] + 1)
                self.send_con_perdidas_tcp(ack_segment)
                self.receive_buffer += parsed["data"]

        result = self.receive_buffer[:bytes_to_receive]
        self.receive_buffer = self.receive_buffer[bytes_to_receive:]
        self.bytes_received += len(result)
        if self.bytes_received >= self.message_length:
            self.message_length = 0
            self.bytes_received = 0
            self.receive_buffer = b""
        return result

    def close(self):
        # FIN simplificado, igual que antes
        if not self.conectado:
            return
        fin_segment = self.create_segment(fin=1, seq=self.num_seq)
        self.send_con_perdidas_tcp(fin_segment)
        self.sock.close()
        self.conectado = False

    def recv_close(self):
        if not self.conectado:
            return
        fin_data, _ = self.recv_con_perdidas_tcp()
        fin_parsed = self.parse_segment(fin_data)
        if fin_parsed and fin_parsed["fin"] == 1:
            ack_segment = self.create_segment(ack=1, seq=fin_parsed["seq"] + 1)
            self.send_con_perdidas_tcp(ack_segment)
        self.sock.close()
        self.conectado = False
