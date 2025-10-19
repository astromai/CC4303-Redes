"""
Prueba 2: Integridad de datos SIN pérdidas con control de congestión
"""
import SocketTCP
import hashlib

address = ("localhost", 8001)

# Leer archivo
print("[INFO] Leyendo archivo 100text.txt...")
with open("100text.txt", "rb") as f:
    content = f.read()

hash_original = hashlib.md5(content).hexdigest()
print(f"[INFO] Tamaño: {len(content)} bytes")
print(f"[INFO] MD5 original: {hash_original}\n")

# Crear cliente
client_socketTCP = SocketTCP.SocketTCP()
client_socketTCP.connect(address)
print("[INFO] Conectado al servidor\n")

# Enviar con Go Back-N + Control de Congestión
print("[INFO] Enviando archivo con Go Back-N + Control de Congestión...")
client_socketTCP.send(content, mode="go_back_n", debug=False)

print(f"\n[RESULTADO] Segmentos enviados: {client_socketTCP.number_of_sent_segments}")

# Enviar señal de FIN para indicar fin de transmisión
client_socketTCP.close()

print("[INFO] Transmisión completada")
print("\n✓ Prueba 2 completada - Verifique que los MD5 coincidan")
