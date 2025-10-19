# Tests para Go Back-N (Parte 2)

## Archivos de prueba creados:
- `test_client.py` - Cliente para tests básicos
- `test_server.py` - Servidor para tests básicos  
- `cliente.py` - Cliente que lee de stdin
- `servidor.py` - Servidor que muestra en pantalla

## Test 1: Tests Básicos (SIN pérdidas)

### Paso 1: Ejecutar servidor
En una terminal:
```powershell
cd c:\Users\leori\Desktop\CC4303-Redes\controlCongestion
python test_server.py
```

### Paso 2: Ejecutar cliente
En otra terminal:
```powershell
cd c:\Users\leori\Desktop\CC4303-Redes\controlCongestion
python test_client.py
```

### Resultados esperados:
- ✓ Test 1: PASSED (16 bytes)
- ✓ Test 2: PASSED (19 bytes)
- ✓ Test 3: PASSED (19 bytes en 2 partes)

---

## Test 2: Transferencia desde archivo (SIN pérdidas)

### Paso 1: Ejecutar servidor
```powershell
cd c:\Users\leori\Desktop\CC4303-Redes\controlCongestion
python servidor.py
```

### Paso 2: Ejecutar cliente con archivo
```powershell
cd c:\Users\leori\Desktop\CC4303-Redes\controlCongestion
Get-Content ../stop&wait/EntregaFinal/archivo_prueba.txt | python cliente.py
```

O crear un archivo de prueba:
```powershell
echo "Este es un mensaje de prueba para Go Back-N" | python cliente.py
```

---

## Test 3: CON pérdidas (manual)

### Opción A: Modificar SocketTCP.py temporalmente
Agregar pérdidas en `send_using_go_back_n`:
```python
# En lugar de: udp_socket.sendto(segment, self.destino, timer_index=window_index)
# Usar: self.send_con_perdidas_tcp(segment, loss_probability=20)  # 20% pérdida
```

### Opción B: Usar netem (Linux)
```bash
sudo tc qdisc add dev lo root netem loss 20%
```

### Ejecutar pruebas:
Repetir Test 1 o Test 2 con pérdidas activadas.

**Comportamiento esperado con pérdidas:**
- El protocolo debe retransmitir automáticamente los segmentos perdidos
- Todos los tests deben seguir pasando (PASSED)
- Puede tardar más tiempo debido a retransmisiones

---

## Estructura esperada:

```
controlCongestion/
├── SocketTCP.py          (Go Back-N implementado)
├── CongestionControl.py  (Parte 1 - listo)
├── test_client.py        (Tests básicos)
├── test_server.py        (Tests básicos)
├── cliente.py            (Lee de stdin)
├── servidor.py           (Muestra en pantalla)
└── utils/
    ├── socketUDP.py
    └── slidingWindowCC.py
```

---

---

## Test 4: Control de Congestión (Parte 3)

### Descripción:
Ahora `send_using_go_back_n` implementa control de congestión TCP Tahoe:
- **MSS = 8 bytes** (antes era 16)
- **window_size dinámico** controlado por `CongestionControl`
- **Slow Start**: cwnd crece exponencialmente (cwnd += MSS por cada ACK)
- **Congestion Avoidance**: cwnd crece linealmente al alcanzar ssthresh
- **Timeout**: ssthresh = cwnd/2, cwnd = MSS, volver a slow start

### Paso 1: Ejecutar servidor
```powershell
cd c:\Users\leori\Desktop\CC4303-Redes\controlCongestion
python test_congestion_server.py
```

### Paso 2: Ejecutar cliente con DEBUG
```powershell
cd c:\Users\leori\Desktop\CC4303-Redes\controlCongestion
python test_congestion_control.py
```

### Qué observar:
- **Inicialización**: cwnd=8 bytes, window_size=1 segmento
- **Slow Start**: window_size crece: 1 → 2 → 4 → 8 (exponencial)
- **Estado**: "slow_start" inicialmente
- **Si hay timeout**: ssthresh se establece, cwnd vuelve a MSS
- **Congestion Avoidance**: crecimiento +1 MSS por ronda (si se alcanza ssthresh)

### Test respuestas esperadas:
**P: ¿Qué valor tiene window_size al inicio?**
R: **1 segmento** (porque cwnd = MSS = 8 bytes, entonces cwnd/MSS = 1)

**P: ¿Cómo evoluciona la ventana sin pérdidas?**
R: En slow start: 1 → 2 → 4 → 8 → 16... (se duplica cada ronda)

**P: ¿Qué pasa cuando hay timeout?**
R: ssthresh = cwnd/2, cwnd = MSS, window_size = 1, estado = "slow_start"

---

## Notas:
- Asegúrate de ejecutar primero el servidor y luego el cliente
- Los tests usan `mode="go_back_n"` en los métodos `send()` y `recv()`
- El handshake y close siguen usando Stop & Wait (como debe ser)
- Para ver evolución de control de congestión, usa `debug=True` en `send()`
