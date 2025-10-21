import random
import time
from utils.socketUDP import SocketUDP
from utils.slidingWindowCC import SlidingWindowCC
from CongestionControl import CongestionControl

class SocketTCP:
    def __init__(self):
        #socket UDP
        self.socketUDP = SocketUDP()
        self.destino = (None, None)
        self.origen = (None, None)
        self.num_seq = 0
        self.timeout = 0.3  # Segundos
        self.conectado = False
        self.buffer_size = 16  # Tamaño máximo de paquete
        self.message_length = 0  # Largo del mensaje que se está recibiendo
        self.bytes_received = 0  # Bytes recibidos hasta el momento
        self.receive_buffer = b""  # Buffer para datos recibidos
        self.number_of_sent_segments = 0

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
        self.socketUDP.bind(address)

    def connect(self, address):
        self.destino = address
        self.num_seq = random.randint(0, 100)
        
        syn_segment = self.create_segment(syn=1, seq=self.num_seq)
        
        # Stop & Wait para el SYN
        while True:
            self.socketUDP.sendto(syn_segment, self.destino, timer_index=0)
            self.socketUDP.settimeout(self.timeout)
            
            try:
                response, server_address = self.socketUDP.recvfrom(1024)
                parsed_response = self.parse_segment(response)

                if parsed_response and parsed_response["syn"] == 1 and parsed_response["ack"] == 1:
                    self.num_seq += 1
                    ack_segment = self.create_segment(ack=1, seq=self.num_seq)
                    self.socketUDP.sendto(ack_segment, server_address, timer_index=0)
                    self.destino = server_address
                    self.conectado = True
                    break
            except TimeoutError:
                continue

    def accept(self):
        data, client_address = self.socketUDP.recvfrom(1024)
        parsed_data = self.parse_segment(data)

        if parsed_data and parsed_data["syn"] == 1:
            new_socket = SocketTCP()
            new_socket.destino = client_address
            new_socket.origen = (self.origen[0], self.origen[1] + 1)
            new_socket.socketUDP.bind(new_socket.origen)
            new_socket.num_seq = random.randint(0, 100)

            syn_ack = new_socket.create_segment(syn=1, ack=1, seq=new_socket.num_seq)
            
            # Stop & Wait para el SYN-ACK
            while True:
                new_socket.socketUDP.sendto(syn_ack, client_address, timer_index=0)
                new_socket.socketUDP.settimeout(new_socket.timeout)
                
                try:
                    ack_data, _ = new_socket.socketUDP.recvfrom(1024)
                    ack_parsed = self.parse_segment(ack_data)

                    if ack_parsed and ack_parsed["ack"] == 1:
                        new_socket.conectado = True
                        new_socket.num_seq += 1
                        return new_socket, new_socket.origen
                except TimeoutError:
                    continue
            
        return None, None

    def send_con_perdidas_tcp(self, segment, loss_probability=0, start_timer=True):
        random_number = random.randint(0, 100)
        if random_number >= loss_probability:
            if start_timer:
                self.socketUDP.sendto(segment, self.destino, timer_index=0)
            else:
                # Enviar sin iniciar timer (para uso interno de socketUDP)
                self.socketUDP.socket_udp.sendto(segment, self.destino)
        else:
            print(f"Oh no, se perdió segmento: {segment[:20]}...")

    def recv_con_perdidas_tcp(self, loss_probability=0):
        # Similar a recv_con_perdidas de utils pero para segmentos TCP
        while True:
            buffer, address = self.socketUDP.recvfrom(1024)
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
            self.socketUDP.settimeout(self.timeout)
            
            try:
                ack_data, _ = self.recv_con_perdidas_tcp()
                ack_parsed = self.parse_segment(ack_data)
                
                if ack_parsed and ack_parsed["ack"] == 1 and ack_parsed["seq"] == self.num_seq + 1:
                    self.num_seq += 1
                    break
            except TimeoutError:
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
                
                try:
                    ack_data, _ = self.recv_con_perdidas_tcp()
                    ack_parsed = self.parse_segment(ack_data)
                    
                    if ack_parsed and ack_parsed["ack"] == 1 and ack_parsed["seq"] == self.num_seq + 1:
                        self.num_seq += 1
                        break
                except TimeoutError:
                    continue
            
            byte_inicial += self.buffer_size

    def recv_using_stop_and_wait(self, buff_size):
        if not self.conectado:
            return b""
        
        # Si no hemos recibido nada aún, esperar el message_length
        if self.bytes_received == 0 and self.message_length == 0:
            # Limpiar buffer antes de recibir nuevo mensaje
            self.receive_buffer = b""
            
            # Recibir el primer segmento con el largo del mensaje
            while True:
                data, _ = self.recv_con_perdidas_tcp()
                length_parsed = self.parse_segment(data)
                
                # Caso borde: servidor reenvía SYN-ACK porque perdió nuestro ACK
                if length_parsed and length_parsed["syn"] == 1 and length_parsed["ack"] == 1:
                    ack_segment = self.create_segment(ack=1, seq=length_parsed["seq"] + 1)
                    self.send_con_perdidas_tcp(ack_segment, start_timer=False)
                    continue
                
                if length_parsed and length_parsed["data"]:
                    # Enviar ACK
                    ack_segment = self.create_segment(ack=1, seq=length_parsed["seq"] + 1)
                    self.send_con_perdidas_tcp(ack_segment, start_timer=False)
                    
                    # Guardar el largo del mensaje
                    self.message_length = int(length_parsed["data"].decode())
                    break
        
        # Recibir datos hasta completar buff_size o message_length
        bytes_to_receive = min(buff_size, self.message_length - self.bytes_received)
        
        while len(self.receive_buffer) < bytes_to_receive:
            # Recibir siguiente segmento
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

    def send_using_go_back_n(self, message, debug=False):
        if not self.conectado:
            return
        
        # Configurar timeout ANTES de enviar cualquier cosa
        self.socketUDP.settimeout(self.timeout)
        
        MSS = 8
        congestion_control = CongestionControl(MSS)
        
        message_length_bytes = str(len(message)).encode()
        data_list = [message_length_bytes] + [message[i:i+MSS] for i in range(0, len(message), MSS)]

        window_size = congestion_control.get_MSS_in_cwnd()
        data_window = SlidingWindowCC(window_size, data_list, self.num_seq)
        
        # Variable para rastrear el último seq enviado
        initial_seq = self.num_seq
        total_bytes = len(message_length_bytes) + len(message)
                
        def send_range(start_idx, end_idx_exclusive):
            for i in range(start_idx, end_idx_exclusive):
                seg_data = data_window.get_data(i)
                seg_seq = data_window.get_sequence_number(i)
                if seg_data is None:
                    break
                segment = self.create_segment(seq=seg_seq, data=seg_data)
                self.socketUDP.stop_timer(timer_index=0)
                self.socketUDP.sendto(segment, self.destino, timer_index=0)
                self.number_of_sent_segments += 1
                if debug:
                    print(f"[DEBUG] Enviado segmento: seq={seg_seq}, len={len(seg_data)}")

        # Enviar ventana inicial
        send_range(0, window_size)

        if debug:
            print(f"[DEBUG] Estado inicial:")
            print(f"  cwnd = {congestion_control.get_cwnd()} bytes ({window_size} MSS)")
            print(f"  ssthresh = {congestion_control.get_ssthresh()}")
            print(f"  state = {congestion_control.state}")
            print(f"  data_window:\n{data_window}\n")

        while True:
            try:
                ack_bytes, _ = self.socketUDP.recvfrom(1024)
                ack = self.parse_segment(ack_bytes)
                if not ack or ack["ack"] != 1:
                    continue

                ack_seq = ack["seq"]

                # Calcular cuántos elementos de la ventana fueron reconocidos
                steps_to_move = 0
                for i in range(window_size):
                    seg_seq = data_window.get_sequence_number(i)
                    seg_data = data_window.get_data(i)
                    if seg_seq is None or seg_data is None:
                        break
                    # El ACK reconoce hasta (pero no incluyendo) ack_seq
                    if seg_seq + len(seg_data) <= ack_seq:
                        steps_to_move += 1
                    else:
                        break

                # Mover ventana si hay elementos reconocidos
                if steps_to_move > 0:
                    data_window.move_window(steps_to_move)

                # Evento ACK recibido
                congestion_control.event_ack_received()
                new_window_size = congestion_control.get_MSS_in_cwnd()
                old_window_size = window_size
                window_size = new_window_size
                
                # Caso borde: ventana disminuye y ACK está fuera de ella
                # Mover ventana hasta que el ACK caiga dentro o terminemos
                while (window_size < old_window_size and 
                    data_window.get_sequence_number(window_size - 1) is not None and
                    data_window.get_sequence_number(window_size - 1) + 
                    len(data_window.get_data(window_size - 1)) <= ack_seq):
                    data_window.move_window(1)
                    steps_to_move += 1
                
                data_window.update_window_size(new_window_size)

                if debug:
                    print(f"[DEBUG] ACK {ack_seq} | steps_moved={steps_to_move} | "
                        f"cwnd={congestion_control.get_cwnd()} ({window_size} MSS) | "
                        f"state={congestion_control.state}")
                    
                if steps_to_move > 0:
                    # La ventana se movió, enviar desde donde quedó el nuevo contenido
                    start_idx = max(0, old_window_size - steps_to_move)
                    send_range(start_idx, window_size)
                elif window_size > old_window_size:
                    # La ventana solo creció sin moverse
                    send_range(old_window_size, window_size)

                # Verificar si terminamos
                if data_window.get_data(0) is None:
                    break

            except TimeoutError:
                # Evento Timeout
                congestion_control.event_timeout()
                new_window_size = congestion_control.get_MSS_in_cwnd()
                old_window_size = window_size
                window_size = new_window_size
                data_window.update_window_size(new_window_size)
                
                if debug:
                    print(f"[DEBUG] Timeout! cwnd={congestion_control.get_cwnd()} "
                        f"ssthresh={congestion_control.get_ssthresh()} "
                        f"state={congestion_control.state}")
                
                # Reenviar toda la ventana desde el inicio
                send_range(0, window_size)

        if debug:
            print("[DEBUG] Envío completado correctamente.")
        
        # Actualizar num_seq al final
        self.num_seq = initial_seq + total_bytes


    def recv_using_go_back_n(self, buff_size):
        if not self.conectado:
            return b""
        
        if self.bytes_received == 0 and self.message_length == 0:
            self.receive_buffer = b""
            
            while True:
                data, _ = self.recv_con_perdidas_tcp()
                length_parsed = self.parse_segment(data)
                
                if length_parsed and length_parsed["syn"] == 1 and length_parsed["ack"] == 1:
                    ack_segment = self.create_segment(ack=1, seq=length_parsed["seq"] + 1)
                    self.send_con_perdidas_tcp(ack_segment, start_timer=False)
                    continue
                
                if length_parsed and length_parsed["data"]:
                    ack_segment = self.create_segment(ack=1, seq=length_parsed["seq"] + len(length_parsed["data"]))
                    self.send_con_perdidas_tcp(ack_segment, start_timer=False)
                    
                    self.message_length = int(length_parsed["data"].decode())
                    self.num_seq = length_parsed["seq"] + len(length_parsed["data"])
                    break
        
        expected_seq = self.num_seq
        bytes_to_receive = min(buff_size, self.message_length - self.bytes_received)

        while len(self.receive_buffer) < bytes_to_receive:
            data, _ = self.recv_con_perdidas_tcp()
            data_parsed = self.parse_segment(data)
            
            if data_parsed:
                if data_parsed["seq"] == expected_seq:
                    self.receive_buffer += data_parsed["data"]
                    expected_seq += len(data_parsed["data"])
                    ack_segment = self.create_segment(ack=1, seq=expected_seq)
                    self.send_con_perdidas_tcp(ack_segment, start_timer=False)
                else:
                    ack_segment = self.create_segment(ack=1, seq=expected_seq)
                    self.send_con_perdidas_tcp(ack_segment, start_timer=False)
        
        result = self.receive_buffer[:bytes_to_receive]
        self.receive_buffer = self.receive_buffer[bytes_to_receive:]
        self.bytes_received += len(result)
        if self.bytes_received >= self.message_length:
            self.message_length = 0
            self.bytes_received = 0
            self.receive_buffer = b""
        self.num_seq = expected_seq
        return result

    def send(self, message, mode="stop_and_wait", debug=False):
        if mode == "stop_and_wait":
            self.send_using_stop_and_wait(message)
        elif mode == "go_back_n":
            self.send_using_go_back_n(message, debug=debug)
        
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
            self.socketUDP.stop_timer(timer_index=0)
            self.send_con_perdidas_tcp(fin_segment)
            self.socketUDP.settimeout(self.timeout)
            
            try:
                ack_data, _ = self.recv_con_perdidas_tcp()
                ack_parsed = self.parse_segment(ack_data)
                
                if ack_parsed and ack_parsed["ack"] == 1 and ack_parsed["seq"] == self.num_seq + 1:
                    self.num_seq += 1
                    ack_received = True
                    break
            except TimeoutError:
                timeout_count += 1
                continue
        
        # Si no recibimos ACK después de 3 timeouts, asumir que la contraparte se cerró
        if not ack_received:
            self.conectado = False
            self.socketUDP.close()
            return
        
        # Esperar FIN del otro lado - hasta 3 timeouts
        timeout_count = 0
        fin_received = False
        fin_seq = 0
        
        while timeout_count < 3:
            self.socketUDP.settimeout(self.timeout)
            
            try:
                fin_data, _ = self.recv_con_perdidas_tcp()
                fin_parsed = self.parse_segment(fin_data)
                
                if fin_parsed and fin_parsed["fin"] == 1:
                    fin_seq = fin_parsed["seq"]
                    fin_received = True
                    break
            except TimeoutError:
                timeout_count += 1
                self.socketUDP.stop_timer(timer_index=0)
                # Reenviar nuestro FIN por si se perdió
                self.send_con_perdidas_tcp(fin_segment)
                continue
        
        # Si no recibimos FIN, asumir que la contraparte se cerró
        if not fin_received:
            self.conectado = False
            self.socketUDP.close()
            return
        
        # Enviar ACK final 3 veces con timeout entre cada envío
        final_ack = self.create_segment(ack=1, seq=fin_seq + 1)
        for i in range(3):
            self.send_con_perdidas_tcp(final_ack, start_timer=False)
            if i < 2:
                time.sleep(self.timeout)
        
        # Cerrar socket y limpiar estado
        self.conectado = False
        self.socketUDP.close()

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
            self.socketUDP.stop_timer(timer_index=0)
            self.send_con_perdidas_tcp(fin_segment)
            self.socketUDP.settimeout(self.timeout)
            
            try:
                final_ack_data, _ = self.recv_con_perdidas_tcp()
                final_ack_parsed = self.parse_segment(final_ack_data)
                
                if final_ack_parsed and final_ack_parsed["ack"] == 1 and final_ack_parsed["seq"] == self.num_seq + 1:
                    break
            except TimeoutError:
                timeout_count += 1
                continue
        
        # Si no recibimos ACK después de 3 timeouts, asumir que la contraparte se cerró
        
        # Cerrar socket y limpiar estado
        self.conectado = False
        self.socketUDP.close()
