# Guía de Pruebas - Control de Congestión

## 📋 Requisitos Previos
- Tener el archivo `100text.txt` en la carpeta `controlCongestion/`
- Python 3 instalado
- Acceso a `netem` (Linux) o pérdidas manuales

---

## 🧪 Prueba 2: Integridad de Datos SIN Pérdidas

**Objetivo:** Verificar que los datos llegan íntegros con control de congestión

### Ejecutar:
```bash
# Terminal 1
cd ~/Desktop/CC4303-Redes/controlCongestion
python prueba2_servidor.py

# Terminal 2
python prueba2_cliente.py
```

### ✅ Criterio de éxito:
- Los hash MD5 deben coincidir entre cliente y servidor
- Mensaje: "✓ Prueba 2 completada - Verifique que los MD5 coincidan"

---

## 🧪 Prueba 3: Observar Control de Congestión SIN Pérdidas

**Objetivo:** Ver evolución de cwnd sin pérdidas inducidas

### Ejecutar:
```bash
# Terminal 1
python prueba3_servidor.py

# Terminal 2
python prueba3_cliente.py
```

### 📊 Qué observar:
- **Inicialización:** cwnd=8, window_size=1
- **Evolución:** window_size crece 1→2→3→4→5... (crecimiento lineal en número de ACKs)
- **Estado:** Permanece en "slow_start" (sin timeout)
- **ssthresh:** Permanece en None (no hay timeout)
- **Timeouts espontáneos:** Verificar si ocurren (probablemente NO sin pérdidas)

### 📝 Para el informe:
Anote:
- ¿Ocurrieron timeouts espontáneos? (probablemente NO)
- Valor final de cwnd y window_size
- Estado final (debería ser "slow_start")

---

## 🧪 Prueba 4: Control de Congestión CON Pérdidas Inducidas

**Objetivo:** Observar cómo responde el control de congestión a pérdidas

### Activar pérdidas (Linux con netem):
```bash
sudo tc qdisc add dev lo root netem loss 20%
```

### Ejecutar:
```bash
# Terminal 1
python prueba3_servidor.py

# Terminal 2
python prueba3_cliente.py
```

### 📊 Qué observar en el debug:
- **Timeouts:** Mensaje "[DEBUG CC] ¡TIMEOUT! Reenviar desde base=X"
- **Después de timeout:**
  - ssthresh se establece (cwnd/2 del momento del timeout)
  - cwnd vuelve a MSS (8 bytes)
  - window_size vuelve a 1
  - Estado vuelve a "slow_start"
- **Recuperación:** Ventana crece hasta ssthresh, luego pasa a "congestion_avoidance"
- **Congestion Avoidance:** Crecimiento más lento (+1 MSS por ronda completa)

### 📝 Para el informe:
Anote:
- Valor de ssthresh después del primer timeout
- Diferencia en crecimiento de ventana: slow start vs congestion avoidance
- Tiempo de recuperación después de timeout

### Desactivar pérdidas:
```bash
sudo tc qdisc del dev lo root
```

---

## 🧪 Prueba 5: Comparación de Rendimiento (20% pérdida)

**Objetivo:** Comparar Go Back-N CON vs SIN control de congestión

### Preparación:
1. Activar pérdidas del 20%:
   ```bash
   sudo tc qdisc add dev lo root netem loss 20%
   ```

### Ejecutar 5 veces:
```bash
# Terminal 1 (dejar corriendo)
python prueba5_servidor.py

# Terminal 2 (ejecutar 5 veces)
python prueba5_cliente.py
# Anotar: tiempo y segmentos_enviados
# Ejecutar 5 veces y promediar
```

### 📊 Resultados esperados:
Cada ejecución mostrará:
- **Tiempo de transmisión:** X.XX segundos
- **Segmentos enviados:** YYYY
- **Overhead:** Z.ZZ x (cuántas veces más que el mínimo teórico)

### 📝 Para el informe - Tabla de resultados:

#### CON Control de Congestión (esta actividad):
| Prueba | Tiempo (s) | Segmentos | Overhead |
|--------|------------|-----------|----------|
| 1      |            |           |          |
| 2      |            |           |          |
| 3      |            |           |          |
| 4      |            |           |          |
| 5      |            |           |          |
| **Promedio** | | | |

#### SIN Control de Congestión (actividad anterior):
| Prueba | Tiempo (s) | Segmentos | Overhead |
|--------|------------|-----------|----------|
| 1      |            |           |          |
| 2      |            |           |          |
| 3      |            |           |          |
| 4      |            |           |          |
| 5      |            |           |          |
| **Promedio** | | | |

### Desactivar pérdidas:
```bash
sudo tc qdisc del dev lo root
```

---

## 📝 Preguntas para el Informe

### Parte 2 - Paso 1:

**1. ¿Por qué Go Back-N puede usar como base Stop & Wait? ¿Qué similitud tienen?**

**Respuesta sugerida:**
- Ambos protocolos usan la misma estructura: enviar segmento → esperar ACK → manejar timeout
- La diferencia es que Stop & Wait maneja 1 segmento a la vez, mientras Go Back-N maneja N segmentos simultáneamente
- Go Back-N es una generalización: usa una ventana deslizante de tamaño N, donde Stop & Wait es el caso especial con N=1
- Ambos usan ACKs para confirmar recepción y retransmiten en caso de timeout
- La lógica de timeout y retransmisión es similar, solo que Go Back-N retransmite desde base en adelante

**2. ¿La función `recv` cambia con SocketUDP y SlidingWindowCC?**

**Respuesta sugerida:**
- NO, el receptor en Go Back-N **no necesita** SocketUDP ni SlidingWindowCC
- Solo el emisor usa estas clases para manejar múltiples timers y la ventana deslizante
- El receptor es más simple: solo acepta segmentos en orden y envía ACKs acumulativos
- Si llega un segmento fuera de orden, lo descarta y reenvía el último ACK
- La función `recv` básica no cambia significativamente

### Prueba 3:

**3. ¿Ocurrieron timeouts espontáneos sin pérdidas inducidas?**

**Respuesta esperada:** 
- [Tu observación aquí]

### Prueba 4:

**4. ¿Cómo responde el control de congestión a los timeouts?**

**Respuesta esperada:**
- ssthresh se establece como cwnd/2
- cwnd vuelve a 1 MSS
- window_size vuelve a 1 segmento
- Estado regresa a "slow_start"
- Crece exponencialmente hasta ssthresh
- Luego pasa a "congestion_avoidance" con crecimiento lineal

### Prueba 5:

**5. ¿Cuál toma menos tiempo: CON o SIN control de congestión?**

**Respuesta esperada:**
- [Comparar promedios de tiempo]
- CON control puede ser más lento inicialmente (ventana pequeña)
- Pero puede recuperarse mejor de pérdidas (evita timeouts repetidos)
- Analizar overhead: cuántos segmentos extra se enviaron

**6. ¿Cuál envía menos segmentos totales?**

**Respuesta esperada:**
- [Comparar promedios de segmentos enviados]
- Menor overhead = mejor eficiencia

---

## 🎯 Checklist Final

- [ ] Prueba 2: Integridad verificada (MD5 coinciden)
- [ ] Prueba 3: Observado sin pérdidas (anotar comportamiento)
- [ ] Prueba 4: Observado con pérdidas (anotar ssthresh, cambios de estado)
- [ ] Prueba 5: 5 ejecuciones CON control de congestión (tabla completa)
- [ ] Comparación con actividad anterior (SIN control de congestión)
- [ ] Respuestas a preguntas teóricas en informe
- [ ] Análisis de resultados

---

## 💡 Notas

- **MSS = 8 bytes** en control de congestión (vs 16 bytes en actividad anterior)
- **Overhead = segmentos_enviados / segmentos_teóricos**
  - Segmentos teóricos = ceil(100KB / 8 bytes) ≈ 12800
- **Netem** solo funciona en Linux. En Windows puedes modificar el código para pérdidas manuales
- Ejecuta `sudo tc qdisc del dev lo root` para limpiar configuración de netem
