import socket
import random
import time

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

    def send(self, message):
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

    def recv(self, buff_size):
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
