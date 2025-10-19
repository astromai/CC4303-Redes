"""
Prueba 3: Observar control de congestión SIN pérdidas inducidas
"""
import SocketTCP

address = ("localhost", 8001)

# Leer archivo
print("[INFO] Leyendo archivo 100text.txt...")
with open("100text.txt", "rb") as f:
    content = f.read()

print(f"[INFO] Tamaño: {len(content)} bytes")
print(f"[INFO] Con MSS=8, son {(len(content) + 7) // 8} segmentos\n")

# Crear cliente
client_socketTCP = SocketTCP.SocketTCP()
client_socketTCP.connect(address)
print("[INFO] Conectado al servidor\n")

print("="*80)
print("[DEBUG] Iniciando envío con control de congestión - Observar evolución de cwnd")
print("="*80)

# Enviar con DEBUG activado
client_socketTCP.send(content, mode="go_back_n", debug=True)

print("\n" + "="*80)
print(f"[RESULTADO] Segmentos enviados: {client_socketTCP.number_of_sent_segments}")
print("="*80)

# Enviar señal de FIN
client_socketTCP.close()
print("\n[INFO] Transmisión completada")
