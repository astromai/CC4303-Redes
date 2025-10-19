"""
Prueba 5: Comparación de tiempo y mensajes - CON control de congestión (20% pérdida)
Ejecutar 5 veces y promediar resultados
"""
import SocketTCP
import time

address = ("localhost", 8001)

# Leer archivo
with open("100text.txt", "rb") as f:
    content = f.read()

print("="*80)
print("PRUEBA 5: Go Back-N CON Control de Congestión (20% pérdida)")
print("="*80)
print(f"Tamaño archivo: {len(content)} bytes")
print(f"Segmentos esperados (MSS=8): {(len(content) + 7) // 8}")
print("\n⚠️  IMPORTANTE: Configure pérdida del 20% en netem antes de ejecutar")
print("    Comando: sudo tc qdisc add dev lo root netem loss 20%")
print("\nPresione Enter cuando esté listo...")
input()

# Conectar
client_socketTCP = SocketTCP.SocketTCP()
client_socketTCP.connect(address)

# Medir tiempo
print("\n[INFO] Iniciando transmisión...")
start_time = time.time()

client_socketTCP.send(content, mode="go_back_n", debug=False)

end_time = time.time()
elapsed = end_time - start_time

# Resultados
print("\n" + "="*80)
print("RESULTADOS:")
print("="*80)
print(f"Tiempo de transmisión: {elapsed:.2f} segundos")
print(f"Segmentos enviados: {client_socketTCP.number_of_sent_segments}")
print(f"Overhead: {client_socketTCP.number_of_sent_segments / ((len(content) + 7) // 8):.2f}x")
print("="*80)

# Enviar señal de FIN
client_socketTCP.close()

print("\n✓ Prueba completada")
print("\nNOTA: Ejecute esto 5 veces y anote los resultados para el informe")
print("      No olvide desactivar netem: sudo tc qdisc del dev lo root")
