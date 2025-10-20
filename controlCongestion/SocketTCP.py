import socket
import random
from utils.slidingWindowCC import SlidingWindowCC
import CongestionControl

class SocketTCP:
    def __init__(self):
        #socket UDP
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.destino = (None, None)
        self.origen = (None, None)
        self.num_seq = 0
        self.timeout = 2  # Segundos
        self.conectado = False
        self.buffer_size = 16  # Tamaño máximo de paquete
        self.message_length = 0  # Largo del mensaje que se está recibiendo
        self.bytes_received = 0  # Bytes recibidos hasta el momento
        self.receive_buffer = b""  # Buffer para datos recibidos
        self.number_of_sent_segments = 0  # Contador de segmentos enviados
        self.expected_seq = None  # Número de secuencia esperado (Go-Back-N)

    @staticmethod
    def create_segment(syn=0, ack=0, fin=0, seq=0, data=bytes()):
        # Crear el header siguiendo el formato del ejemplo
        header = f"{syn}|||{ack}|||{fin}|||{seq}|||"
        
        # Convertir header a bytes y agregar los datos
        header_bytes = header.encode()
        segment = header_bytes + data
        
        return segment

    @staticmethod
    def parse_segment(segment_bytes):
        segment_str = segment_bytes.decode()
        
        # Dividir por el separador, limitando a 5 partes máximo
        # (4 campos del header + 1 para los datos)
        parts = segment_str.split("|||", 4)
        
        if len(parts) < 4:
            return None
        
        # Extraer flags y número de secuencia
        syn = int(parts[0])
        ack = int(parts[1]) 
        fin = int(parts[2])
        seq = int(parts[3])
        
        # Los datos están en la 5ta parte (si existe)
        if len(parts) > 4:
            data = parts[4].encode()
        else:
            data = bytes()
        
        return {
            "syn": syn,
            "ack": ack, 
            "fin": fin,
            "seq": seq,
            "data": data
        }
    
    def bind(self, address):
        self.origen = address
        self.sock.bind(address)

    def connect(self, address):
        self.destino = address
        self.num_seq = random.randint(0, 100)
        
        syn_segment = self.create_segment(syn=1, seq=self.num_seq)
        
        # Stop & Wait para el SYN
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
            new_socket = SocketTCP()
            new_socket.destino = client_address
            new_socket.origen = (self.origen[0], self.origen[1] + 1)
            new_socket.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            new_socket.sock.bind(new_socket.origen)
            new_socket.num_seq = random.randint(0, 100)

            syn_ack = new_socket.create_segment(syn=1, ack=1, seq=new_socket.num_seq)
            
            # Stop & Wait para el SYN-ACK
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
        # Similar a send_con_perdidas de utils pero para segmentos TCP
        random_number = random.randint(0, 100)
        if random_number >= loss_probability:
            self.sock.sendto(segment, self.destino)
        else:
            print(f"Oh no, se perdió segmento: {segment[:20]}...")

    def recv_con_perdidas_tcp(self, loss_probability=0):
        # Similar a recv_con_perdidas de utils pero para segmentos TCP
        while True:
            buffer, address = self.sock.recvfrom(1024)
            random_number = random.randint(0, 100)
            if random_number <= loss_probability:
                continue
            else:
                break
        return buffer, address

    def send_using_stop_and_wait(self, message):
        if not self.conectado:
            return
        
        # Enviar primero el largo del mensaje
        message_length = len(message)
        length_segment = self.create_segment(seq=self.num_seq, data=str(message_length).encode())
        
        # Stop & Wait para el length
        while True:
            self.send_con_perdidas_tcp(length_segment)
            self.sock.settimeout(self.timeout)
            
            try:
                ack_data, _ = self.recv_con_perdidas_tcp()
                ack_parsed = self.parse_segment(ack_data)
                
                if ack_parsed and ack_parsed["ack"] == 1 and ack_parsed["seq"] == self.num_seq + 1:
                    self.num_seq += 1
                    break
            except socket.timeout:
                continue
        
        # Ahora enviar el mensaje en trozos de 16 bytes
        byte_inicial = 0
        
        while byte_inicial < len(message):
            # Obtener trozo de máximo 16 bytes
            max_byte = min(len(message), byte_inicial + self.buffer_size)
            message_slice = message[byte_inicial:max_byte]
            
            # Crear segmento TCP con el trozo
            data_segment = self.create_segment(seq=self.num_seq, data=message_slice)
            
            # Stop & Wait para este segmento
            while True:
                self.send_con_perdidas_tcp(data_segment)
                self.sock.settimeout(self.timeout)
                
                try:
                    ack_data, _ = self.recv_con_perdidas_tcp()
                    ack_parsed = self.parse_segment(ack_data)
                    
                    if ack_parsed and ack_parsed["ack"] == 1 and ack_parsed["seq"] == self.num_seq + 1:
                        self.num_seq += 1
                        break
                except socket.timeout:
                    continue
            
            byte_inicial += self.buffer_size

    def send_using_go_back_n(self, message, debug=False):
        if not self.conectado:
            return

        # Control de congestión (Parte 3) - Tahoe simplificado
        MSS = 8  # bytes
        congestion_controler = CongestionControl.CongestionControl(MSS)

        # Preparar lista de datos con MSS=8: primero largo, luego segmentos
        message_length_bytes = str(len(message)).encode()
        data_list = [message_length_bytes] + [message[i:i+MSS] for i in range(0, len(message), MSS)]

        # window_size inicial desde cwnd/MSS (debe ser 1)
        window_size = congestion_controler.get_MSS_in_cwnd()
        
        if debug:
            print(f"[CC-DEBUG] init: cwnd={congestion_controler.get_cwnd()} bytes, ssthresh={congestion_controler.get_ssthresh()}, state={'slow_start' if congestion_controler.is_state_slow_start() else 'congestion_avoidance'}, window_size={window_size}")

        # Inicializar ventana deslizante con números de secuencia byte-based
        sw = SlidingWindowCC(window_size, data_list, self.num_seq)

        # Banderas de envío por índice de ventana
        sent_flags = [False] * window_size
        total_bytes = sum(len(d) for d in data_list)
        bytes_acked = 0

        # Función auxiliar para actualizar tamaño de ventana por cambios en cwnd
        def refresh_window_size(reason: str):
            nonlocal window_size, sent_flags
            new_wnd_size = congestion_controler.get_MSS_in_cwnd()
            if new_wnd_size < 1:
                new_wnd_size = 1
            if new_wnd_size != window_size:
                if debug:
                    print(f"[CC-DEBUG] {reason}: cwnd={congestion_controler.get_cwnd()} bytes -> window_size {window_size} -> {new_wnd_size}")
                # Actualizar ventana deslizante
                sw.update_window_size(new_wnd_size)
                # Ajustar banderas
                if new_wnd_size > window_size:
                    sent_flags = sent_flags + [False] * (new_wnd_size - window_size)
                else:
                    sent_flags = sent_flags[:new_wnd_size]
                window_size = new_wnd_size

        # Bucle principal hasta acuse de recibo de todos los bytes
        last_progress_report = 0
        
        while bytes_acked < total_bytes:
            # Reportar progreso cada 1000 bytes
            if bytes_acked - last_progress_report >= 1000:
                print(f"[PROGRESO] {bytes_acked}/{total_bytes} bytes ({100*bytes_acked//total_bytes}%)")
                last_progress_report = bytes_acked
                
            # Enviar elementos nuevos en la ventana actual
            for i in range(window_size):
                d = sw.get_data(i)
                if d is None:
                    continue
                if not sent_flags[i]:
                    seq_i = sw.get_sequence_number(i)
                    segment = self.create_segment(seq=seq_i, data=d)
                    self.sock.sendto(segment, self.destino)
                    self.number_of_sent_segments += 1
                    sent_flags[i] = True
                    if debug:
                        print(f"[CC-DEBUG] send: idx={i}, seq={seq_i}, len={len(d)}")

            # Esperar ACKs con timeout
            self.sock.settimeout(self.timeout)
            try:
                ack_bytes, _ = self.sock.recvfrom(1024)
                ack_parsed = self.parse_segment(ack_bytes)
                if not ack_parsed:
                    continue
                if ack_parsed.get("ack", 0) == 1:
                    ack_seq = ack_parsed.get("seq", 0)
                    # calcular cuántos elementos quedan cubiertos por ack_seq
                    advance = 0
                    acked_lengths = []
                    for i in range(window_size):
                        d = sw.get_data(i)
                        if d is None:
                            break
                        seq_i = sw.get_sequence_number(i)
                        if seq_i + len(d) <= ack_seq:
                            acked_lengths.append(len(d))
                            advance += 1
                        else:
                            break

                    if advance > 0:
                        # Por cada segmento efectivamente nuevo acked, informar al control de congestión
                        for _ in range(advance):
                            congestion_controler.event_ack_received()
                        refresh_window_size("ack")

                        bytes_acked += sum(acked_lengths)
                        if debug:
                            print(f"[CC-DEBUG] ack: ack_seq={ack_seq}, advance={advance}, bytes_acked={bytes_acked}/{total_bytes}")
                        sw.move_window(advance)
                        sent_flags = sent_flags[advance:] + [False] * advance
                    # Si no hay avance, es un ACK duplicado - ignorar

            except socket.timeout:
                # Timeout: notificar a control de congestión y retransmitir toda la ventana
                congestion_controler.event_timeout()
                refresh_window_size("timeout")
                if debug:
                    print("[CC-DEBUG] timeout: retransmit window")
                for i in range(window_size):
                    d = sw.get_data(i)
                    if d is None:
                        continue
                    seq_i = sw.get_sequence_number(i)
                    segment = self.create_segment(seq=seq_i, data=d)
                    self.sock.sendto(segment, self.destino)
                    self.number_of_sent_segments += 1
                    sent_flags[i] = True

        # Avanzar número de secuencia global (continuidad)
        self.num_seq = self.num_seq + total_bytes

    def send(self, message, mode="stop_and_wait", debug=False):
        if mode == "stop_and_wait":
            self.send_using_stop_and_wait(message)
        elif mode == "go_back_n":
            self.send_using_go_back_n(message, debug=debug)

    def recv_using_stop_and_wait(self, buff_size):
        if not self.conectado:
            return b""
        
        # Si no hemos recibido nada aún, esperar el message_length
        if self.bytes_received == 0 and self.message_length == 0:
            # Limpiar buffer antes de recibir nuevo mensaje
            self.receive_buffer = b""
            
            # Recibir el primer segmento con el largo del mensaje
            self.sock.settimeout(None)
            while True:
                data, _ = self.recv_con_perdidas_tcp()
                length_parsed = self.parse_segment(data)
                
                # Caso borde: servidor reenvía SYN-ACK porque perdió nuestro ACK
                if length_parsed and length_parsed["syn"] == 1 and length_parsed["ack"] == 1:
                    ack_segment = self.create_segment(ack=1, seq=length_parsed["seq"] + 1)
                    self.send_con_perdidas_tcp(ack_segment)
                    continue
                
                if length_parsed and length_parsed["data"]:
                    # Enviar ACK
                    ack_segment = self.create_segment(ack=1, seq=length_parsed["seq"] + 1)
                    self.send_con_perdidas_tcp(ack_segment)
                    
                    # Guardar el largo del mensaje
                    self.message_length = int(length_parsed["data"].decode())
                    break
        
        # Recibir datos hasta completar buff_size o message_length
        bytes_to_receive = min(buff_size, self.message_length - self.bytes_received)
        
        while len(self.receive_buffer) < bytes_to_receive:
            # Recibir siguiente segmento
            self.sock.settimeout(None)
            data, _ = self.recv_con_perdidas_tcp()
            data_parsed = self.parse_segment(data)
            
            if data_parsed and data_parsed["data"]:
                # Enviar ACK
                ack_segment = self.create_segment(ack=1, seq=data_parsed["seq"] + 1)
                self.send_con_perdidas_tcp(ack_segment)
                
                # Agregar datos al buffer
                self.receive_buffer += data_parsed["data"]
        
        # Retornar los bytes solicitados
        result = self.receive_buffer[:bytes_to_receive]
        self.receive_buffer = self.receive_buffer[bytes_to_receive:]
        self.bytes_received += len(result)
        
        # Si terminamos de recibir todo, reiniciar variables
        if self.bytes_received >= self.message_length:
            self.message_length = 0
            self.bytes_received = 0
            self.receive_buffer = b""
        
        return result

    def recv_using_go_back_n(self, buff_size):
        if not self.conectado:
            return b""

        # Inicializar expected_seq con el primer segmento válido recibido
        if self.bytes_received == 0 and self.message_length == 0:
            self.receive_buffer = b""
            self.sock.settimeout(None)  # Modo bloqueante sin timeout
            while True:
                data, sender = self.recv_con_perdidas_tcp()
                parsed = self.parse_segment(data)
                if not parsed:
                    continue
                # manejar potencial reenvío de SYN-ACK (caso borde)
                if parsed["syn"] == 1 and parsed["ack"] == 1:
                    ack_segment = self.create_segment(ack=1, seq=parsed["seq"] + 1)
                    self.sock.sendto(ack_segment, sender)
                    continue
                # primer segmento de datos esperado
                if self.expected_seq is None:
                    self.expected_seq = parsed["seq"]
                # si coincide, procesar como largo de mensaje
                if parsed["seq"] == self.expected_seq and parsed["data"]:
                    # interpretar largo
                    try:
                        self.message_length = int(parsed["data"].decode())
                    except ValueError:
                        self.message_length = 0
                    self.expected_seq += len(parsed["data"])
                    # enviar ACK acumulativo
                    ack = self.create_segment(ack=1, seq=self.expected_seq)
                    self.sock.sendto(ack, sender)
                    break
                else:
                    # enviar ACK duplicado con el expected actual
                    ack = self.create_segment(ack=1, seq=self.expected_seq)
                    self.sock.sendto(ack, sender)

        # Ya sabemos cuánto debemos recibir. Recibir hasta buff_size o completar mensaje
        remaining = max(0, self.message_length - self.bytes_received)
        bytes_to_receive = min(buff_size, remaining)

        self.sock.settimeout(None)  # Modo bloqueante sin timeout
        while len(self.receive_buffer) < bytes_to_receive:
            data, sender = self.recv_con_perdidas_tcp()
            parsed = self.parse_segment(data)
            if not parsed:
                continue
            if parsed["data"]:
                if parsed["seq"] == self.expected_seq:
                    # en-orden: aceptar y avanzar expected
                    self.receive_buffer += parsed["data"]
                    self.expected_seq += len(parsed["data"])
                # enviar ACK acumulativo (ya sea en-orden o duplicado)
                ack = self.create_segment(ack=1, seq=self.expected_seq)
                self.sock.sendto(ack, sender)

        result = self.receive_buffer[:bytes_to_receive]
        self.receive_buffer = self.receive_buffer[bytes_to_receive:]
        self.bytes_received += len(result)

        if self.bytes_received >= self.message_length:
            # reiniciar estado de recepción para el próximo mensaje
            self.message_length = 0
            self.bytes_received = 0
            self.receive_buffer = b""
            # expected_seq queda para continuar el flujo de bytes

        return result

    def recv(self, buff_size, mode="stop_and_wait"):
        if mode == "stop_and_wait":
            return self.recv_using_stop_and_wait(buff_size)
        elif mode == "go_back_n":
            return self.recv_using_go_back_n(buff_size)

    def close(self):
        # Host A: Inicia el cierre de conexión enviando FIN
        if not self.conectado:
            return
        
        # Enviar FIN
        fin_segment = self.create_segment(fin=1, seq=self.num_seq)
        
        # Stop & Wait para el FIN - hasta 3 timeouts
        timeout_count = 0
        ack_received = False
        
        while timeout_count < 3:
            self.send_con_perdidas_tcp(fin_segment)
            self.sock.settimeout(self.timeout)
            
            try:
                ack_data, _ = self.recv_con_perdidas_tcp()
                ack_parsed = self.parse_segment(ack_data)
                
                if ack_parsed and ack_parsed["ack"] == 1 and ack_parsed["seq"] == self.num_seq + 1:
                    self.num_seq += 1
                    ack_received = True
                    break
            except socket.timeout:
                timeout_count += 1
                continue
        
        # Si no recibimos ACK después de 3 timeouts, asumir que la contraparte se cerró
        if not ack_received:
            self.conectado = False
            self.sock.close()
            return
        
        # Esperar FIN del otro lado - hasta 3 timeouts
        timeout_count = 0
        fin_received = False
        fin_seq = 0
        
        while timeout_count < 3:
            self.sock.settimeout(self.timeout)
            
            try:
                fin_data, _ = self.recv_con_perdidas_tcp()
                fin_parsed = self.parse_segment(fin_data)
                
                if fin_parsed and fin_parsed["fin"] == 1:
                    fin_seq = fin_parsed["seq"]
                    fin_received = True
                    break
            except socket.timeout:
                timeout_count += 1
                # Reenviar nuestro FIN por si se perdió
                self.send_con_perdidas_tcp(fin_segment)
                continue
        
        # Si no recibimos FIN, asumir que la contraparte se cerró
        if not fin_received:
            self.conectado = False
            self.sock.close()
            return
        
        # Enviar ACK final 3 veces con timeout entre cada envío
        final_ack = self.create_segment(ack=1, seq=fin_seq + 1)
        for i in range(3):
            self.send_con_perdidas_tcp(final_ack)
            if i < 2:
                import time
                time.sleep(self.timeout)
        
        # Cerrar socket y limpiar estado
        self.conectado = False
        self.sock.close()

    def recv_close(self):
        # Host B: Maneja el cierre iniciado por el otro lado
        if not self.conectado:
            return
        
        # Esperar FIN del otro lado
        while True:
            fin_data, _ = self.recv_con_perdidas_tcp()
            fin_parsed = self.parse_segment(fin_data)
            
            if fin_parsed and fin_parsed["fin"] == 1:
                # Enviar ACK por el FIN recibido
                ack_segment = self.create_segment(ack=1, seq=fin_parsed["seq"] + 1)
                self.send_con_perdidas_tcp(ack_segment)
                break
        
        # Enviar nuestro propio FIN
        fin_segment = self.create_segment(fin=1, seq=self.num_seq)
        
        # Stop & Wait para nuestro FIN - hasta 3 timeouts
        timeout_count = 0
        
        while timeout_count < 3:
            self.send_con_perdidas_tcp(fin_segment)
            self.sock.settimeout(self.timeout)
            
            try:
                final_ack_data, _ = self.recv_con_perdidas_tcp()
                final_ack_parsed = self.parse_segment(final_ack_data)
                
                if final_ack_parsed and final_ack_parsed["ack"] == 1 and final_ack_parsed["seq"] == self.num_seq + 1:
                    break
            except socket.timeout:
                timeout_count += 1
                continue
        
        # Si no recibimos ACK después de 3 timeouts, asumir que la contraparte se cerró
        
        # Cerrar socket y limpiar estado
        self.conectado = False
        self.sock.close()
