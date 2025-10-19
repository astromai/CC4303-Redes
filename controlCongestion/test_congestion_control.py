import SocketTCP

# Configuración
address = ("localhost", 8001)

# Crear cliente
client_socketTCP = SocketTCP.SocketTCP()

print("=== TEST CONTROL DE CONGESTIÓN ===\n")
print("[INFO] Conectando al servidor...")
client_socketTCP.connect(address)
print(f"[INFO] Conectado a {client_socketTCP.destino}\n")

input("Presione Enter para enviar mensaje con control de congestión...")

# Mensaje largo para ver evolución de cwnd
# Con MSS=8, necesitamos muchos segmentos para ver slow start y congestion avoidance
message = "Este es un mensaje largo para probar el control de congestión TCP Tahoe con Go Back-N. " * 3
message += "Observaremos cómo crece la ventana exponencialmente en slow start. "
message += "Luego veremos crecimiento lineal en congestion avoidance si llegamos a ssthresh."

print(f"\n[INFO] Mensaje a enviar: {len(message)} bytes")
print(f"[INFO] Con MSS=8, esto se divide en {(len(message) + 7) // 8} segmentos\n")
print("="*80)

# Enviar con debug activado para ver evolución de cwnd
client_socketTCP.send(message.encode(), mode="go_back_n", debug=True)

print("="*80)
print("\n[INFO] Mensaje enviado exitosamente")

input("\nPresione Enter para cerrar conexión...")

# Cerrar conexión
client_socketTCP.close()
print("[INFO] Conexión cerrada")
