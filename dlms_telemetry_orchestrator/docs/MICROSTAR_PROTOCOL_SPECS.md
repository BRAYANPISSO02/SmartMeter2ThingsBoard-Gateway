# 📘 MICROSTAR DLMS PROTOCOL SPECIFICATIONS
**Extraído de: 9.2. Microstar DLMS Protocol Guide.pdf**

---

## 1. ARQUITECTURA DEL PROTOCOLO

### Capas DLMS/COSEM
```
┌─────────────────────────────────────┐
│  Application Layer (COSEM)          │  GET/SET/ACTION sobre objetos OBIS
├─────────────────────────────────────┤
│  Application Association (AARQ)     │  Autenticación y negociación
├─────────────────────────────────────┤
│  Data Link Layer (HDLC)             │  Framing, control de flujo
├─────────────────────────────────────┤
│  Physical Layer (TCP/IP)            │  Puerto 3333
└─────────────────────────────────────┘
```

---

## 2. DIRECCIONAMIENTO HDLC

### 2.1 Dirección del Servidor (Medidor)

#### Physical Address
- **Formato**: Últimos 4 dígitos del número de serie
- **Ejemplo**: Serial `000019001234` → Address `1234` (0x04D2 en HEX)
- **Default**: 1234 si no se conoce el serial

#### Logical Address (Server SAP)
- **Valor**: `1` (fijo)
- **Uso**: Siempre es 1 para medidores Microstar

### 2.2 Dirección del Cliente (Software)

| Client SAP | Hex  | Seguridad      | Acceso       | Uso                    |
|------------|------|----------------|--------------|------------------------|
| 16         | 0x10 | Sin password   | Read-Only    | Public Client          |
| 32         | 0x20 | Con password   | Read-Write   | Management Client      |

**⚠️ IMPORTANTE**: En la práctica, hemos observado que el medidor acepta `client_sap = 1` con password.

---

## 3. AUTENTICACIÓN

### 3.1 Niveles de Seguridad

#### Public Access (No Password)
- **Client SAP**: 16 (0x10)
- **Autenticación**: None
- **Acceso**: Solo lectura
- **Uso**: Monitoreo básico

#### LLS (Low Level Security)
- **Client SAP**: 32 (0x20) *o 1 en nuestro caso*
- **Autenticación**: Password ASCII
- **Acceso**: Lectura y escritura
- **Uso**: Configuración y comandos

### 3.2 Password

**Formato del Password:**
```
AC 0C 80 0A 32 32 32 32 32 32 32 32 32 32
│  │  │  │  └─────────────────────────────── Password ASCII (10 bytes)
│  │  │  └─────────────────────────────────── Length (0x0A = 10 bytes)
│  │  └────────────────────────────────────── Type (0x80 = Octet string)
│  └───────────────────────────────────────── Total length (12 bytes)
└──────────────────────────────────────────── Tag (AC = authentication-value)
```

**Password de nuestro medidor:**
- **Medidor 1**: `"2222222222"` (10 caracteres ASCII)
- **Medidor 2**: `"00000000"` (8 caracteres ASCII) - *por confirmar*

**⚠️ Nota del PDF:**
> "Contact the meter distribution agent or Microstar support for the default meter password."

---

## 4. TIMEOUT DE COMUNICACIÓN

### Parámetros de Tiempo
- **Timeout de inactividad**: **180 segundos (3 minutos)**
- **Acción**: El medidor cierra la conexión automáticamente
- **Solución**: Enviar requests periódicos (keepalive) cada ~120 segundos

### Estrategia de Keepalive
```python
# Enviar cualquier GET-REQUEST válido cada 2 minutos
# Por ejemplo, leer el reloj (OBIS 0-0:1.0.0.255)
if time_since_last_request() > 120:
    read_clock()
```

---

## 5. INTERFACE CLASSES (Tipos de Objetos)

| Class ID | Nombre            | Descripción                              | Ejemplo OBIS            |
|----------|-------------------|------------------------------------------|-------------------------|
| 1        | Data              | Datos sin unidades                       | 0-0:96.1.0.255 (Serial) |
| 3        | Register          | Datos con scaler/unit                    | 1-1:32.7.0 (Voltage)    |
| 4        | Extended Register | Datos con capture time                   | 1-1:1.6.0 (Max Demand)  |
| 5        | Demand Register   | Demanda actual                           | 1-1:1.4.0 (Demand)      |
| 7        | Profile Generic   | Load profile, event logs                 | 1-0:99.1.0.255 (Profile)|
| 8        | Clock             | Reloj del medidor                        | 0-0:1.0.0.255 (Clock)   |

---

## 6. SECUENCIA DE COMUNICACIÓN

### 6.1 Fase 1: HDLC Data Link Setup

```
Cliente                           Servidor (Medidor)
  │                                      │
  ├──────── SNRM ─────────────────────>│  Set Normal Response Mode
  │         (Solicita abrir enlace)     │  - Propone parámetros HDLC
  │                                      │
  │<──────── UA ─────────────────────── │  Unnumbered Acknowledgment
  │         (Acepta enlace)              │  - Confirma parámetros
  │                                      │
```

**Parámetros HDLC Negociados:**
```
05 02 00 80        Max info field transmit: 128 bytes
06 02 00 80        Max info field receive: 128 bytes
07 04 00 00 00 01  Window size transmit: 1
08 04 00 00 00 01  Window size receive: 1
```

### 6.2 Fase 2: Application Association

```
Cliente                           Servidor (Medidor)
  │                                      │
  ├──────── AARQ ─────────────────────>│  Association Request
  │         - Application context        │  - Incluye credenciales
  │         - Conformance block          │  - Capabilities
  │         - Authentication value       │
  │                                      │
  │<──────── AARE ──────────────────────│  Association Response
  │         - Result: 0x00 = Accepted    │
  │         - Diagnostic                 │
  │                                      │
```

**AARQ Frame Structure:**
```
60 ... E0 ...          Application PDU
  A1 ...               Application context name (LN referencing)
  BE ...               User information
    04 ...             AARQ APDU
      8A 02 07 80      Conformance block
      AC 0C 80 0A ...  Authentication value (password)
```

**AARE Result Codes:**
| Code | Significado                    |
|------|--------------------------------|
| 0x00 | Accepted                       |
| 0x01 | Rejected (permanent)           |
| 0x02 | Rejected (transient)           |

### 6.3 Fase 3: Operaciones COSEM

```
Cliente                           Servidor (Medidor)
  │                                      │
  ├──────── GET-REQUEST ──────────────>│  Leer objeto OBIS
  │                                      │
  │<──────── GET-RESPONSE ───────────── │  Valor del objeto
  │                                      │
  ├──────── SET-REQUEST ──────────────>│  Escribir objeto OBIS
  │                                      │
  │<──────── SET-RESPONSE ───────────── │  Confirmación
  │                                      │
  ├──────── ACTION-REQUEST ───────────>│  Ejecutar método
  │                                      │
  │<──────── ACTION-RESPONSE ──────────│  Resultado
  │                                      │
```

### 6.4 Fase 4: Cierre de Conexión

```
Cliente                           Servidor (Medidor)
  │                                      │
  ├──────── DISC ─────────────────────>│  Disconnect
  │                                      │
  │<──────── UA ─────────────────────── │  Confirmation
  │                                      │
```

---

## 7. CÓDIGOS OBIS COMUNES

### 7.1 Información del Medidor
```
0-0:96.1.0.255   Serial Number              (Class 1 - Data)
0-0:42.0.0.255   Firmware Version           (Class 1 - Data)
0-0:1.0.0.255    Clock                      (Class 8 - Clock)
```

### 7.2 Valores Instantáneos (Fase A)
```
1-1:32.7.0       Voltage (V)                (Class 3 - Register)
1-1:31.7.0       Current (A)                (Class 3 - Register)
1-1:14.7.0       Frequency (Hz)             (Class 3 - Register)
1-1:1.7.0        Active Power (+P) (W)      (Class 3 - Register)
1-1:2.7.0        Active Power (-P) (W)      (Class 3 - Register)
1-1:3.7.0        Reactive Power (+Q) (VAr)  (Class 3 - Register)
1-1:4.7.0        Reactive Power (-Q) (VAr)  (Class 3 - Register)
1-1:9.7.0        Apparent Power (VA)        (Class 3 - Register)
```

### 7.3 Energía Acumulada
```
1-1:1.8.0        Active Energy Import (Wh)  (Class 3 - Register)
1-1:2.8.0        Active Energy Export (Wh)  (Class 3 - Register)
1-1:3.8.0        Reactive Energy Import     (Class 3 - Register)
1-1:4.8.0        Reactive Energy Export     (Class 3 - Register)
```

### 7.4 Demanda Máxima
```
1-1:1.6.0        Max Demand (+P)            (Class 4 - Extended Register)
1-1:2.6.0        Max Demand (-P)            (Class 4 - Extended Register)
```

### 7.5 Perfiles y Logs
```
1-0:99.1.0.255   Load Profile               (Class 7 - Profile Generic)
0-0:99.98.0.255  Event Log                  (Class 7 - Profile Generic)
```

---

## 8. FORMATO DE FRAME HDLC

### Estructura General
```
┌────────┬────────┬────────┬────────┬────────┬────────┬────────┐
│  Flag  │ Format │Control │   HCS  │  Data  │   FCS  │  Flag  │
│  0x7E  │  A0 XX │   XX   │ XX XX  │  ...   │ XX XX  │  0x7E  │
└────────┴────────┴────────┴────────┴────────┴────────┴────────┘
```

### Detalles de Campos

#### Format & Length (A0 XX)
- **A0**: HDLC type 3 format
- **XX**: Length of frame (includes format, control, HCS)

#### Control Field
| Tipo      | Formato  | Descripción                    |
|-----------|----------|--------------------------------|
| SNRM      | 93       | Set Normal Response Mode       |
| UA        | 73       | Unnumbered Acknowledgment      |
| DISC      | 53       | Disconnect                     |
| I-frame   | 10, 30   | Information frame (segmented)  |
| RR        | 11, 31   | Receive Ready                  |

#### HCS (Header Check Sequence)
- **Longitud**: 2 bytes
- **Algoritmo**: CRC-16 sobre format+control+addresses
- **Polinomio**: 0x1021

#### FCS (Frame Check Sequence)
- **Longitud**: 2 bytes
- **Algoritmo**: CRC-16 sobre todo excepto flags
- **Polinomio**: 0x1021

---

## 9. EJEMPLO COMPLETO: LECTURA DE VOLTAJE

### Comando Completo
```python
# 1. Conectar TCP
socket.connect(('192.168.1.128', 3333))

# 2. Enviar SNRM
snrm = bytes.fromhex('7E A0 07 03 03 93 8C 11 7E')
socket.send(snrm)

# 3. Recibir UA
ua = socket.recv(256)
# Esperado: 7E A0 1E 03 03 73 ...

# 4. Enviar AARQ con password "2222222222"
aarq = bytes.fromhex(
    '7E A0 46 03 03 10 ...'  # HDLC header
    '60 ... E0 ...'           # Application PDU
    'AC 0C 80 0A 32 32 32 32 32 32 32 32 32 32'  # Password
    '... 7E'
)
socket.send(aarq)

# 5. Recibir AARE
aare = socket.recv(256)
# Verificar result code = 0x00

# 6. Enviar GET-REQUEST para voltaje (1-1:32.7.0)
get_voltage = bytes.fromhex(
    '7E A0 1E 03 03 10 ...'
    'C0 01 C1 00 01 01 20 07 00 FF 02 00'  # OBIS 1-1:32.7.0
    '... 7E'
)
socket.send(get_voltage)

# 7. Recibir GET-RESPONSE
response = socket.recv(256)
# Parse response data

# 8. Cerrar con DISC
disc = bytes.fromhex('7E A0 08 02 03 03 53 09 B1 7E')
socket.send(disc)

# 9. Recibir UA final
final_ua = socket.recv(256)

socket.close()
```

---

## 10. ERRORES COMUNES Y SOLUCIONES

### 10.1 "Invalid HDLC frame boundary"

**Causas:**
1. Buffer TCP corrupto (datos de frame anterior)
2. Medidor respondió con error (7E 7E = garbage)
3. Timeout de 180s expiró

**Soluciones:**
```python
# Limpiar buffer antes de cada operación
socket.recv(4096)  # Drenar cualquier dato pendiente

# Verificar timeout
if time_since_connection() > 170:
    reconnect()

# Enviar keepalive cada 2 minutos
if time_since_last_request() > 120:
    send_clock_read()
```

### 10.2 Authentication Failed

**Causas:**
1. Password incorrecto
2. Client SAP incorrecto
3. Longitud de password incorrecta

**Verificar:**
```python
# Password debe ser exacto
password = "2222222222"  # 10 caracteres

# Encoding correcto en AARQ
auth_value = f"AC {len(password)+2:02X} 80 {len(password):02X}"
for char in password:
    auth_value += f" {ord(char):02X}"
```

### 10.3 Timeout en SNRM/UA

**Causas:**
1. Medidor en timeout (esperando 180s)
2. Puerto TCP bloqueado
3. Dirección física incorrecta

**Verificar:**
```bash
# 1. Probar TCP
nc -zv 192.168.1.128 3333

# 2. Esperar 3 minutos
sleep 180

# 3. Verificar dirección física del medidor
# (Últimos 4 dígitos del serial)
```

---

## 11. MEJORES PRÁCTICAS

### 11.1 Manejo de Conexión
```python
class DLMSConnection:
    TIMEOUT = 180  # segundos
    KEEPALIVE_INTERVAL = 120  # segundos
    
    def maintain_connection(self):
        if time.time() - self.last_request > self.KEEPALIVE_INTERVAL:
            self.read_clock()  # Keepalive simple
```

### 11.2 Reintentos
```python
MAX_RETRIES = 3
RETRY_DELAY = 5  # segundos

for attempt in range(MAX_RETRIES):
    try:
        # Limpiar buffer
        self.socket.recv(4096)
        
        # Intentar operación
        result = self.read_meter()
        break
        
    except HDLCError:
        if attempt < MAX_RETRIES - 1:
            time.sleep(RETRY_DELAY)
        else:
            # Reset físico del medidor
            self.request_physical_reset()
```

### 11.3 Logging
```python
# Log de frames en hexadecimal
logger.debug(f"TX: {frame.hex(' ')}")
logger.debug(f"RX: {response.hex(' ')}")

# Log de timestamps para detectar timeouts
logger.info(f"Connected at {time.time()}")
logger.info(f"Last request at {self.last_request_time}")
```

---

## 12. COMPARACIÓN: ESPECIFICACIÓN vs IMPLEMENTACIÓN ACTUAL

| Aspecto                | Especificación PDF     | Implementación Actual | Estado |
|------------------------|------------------------|-----------------------|--------|
| Client SAP (password)  | 32 (0x20)              | 1                     | ⚠️ Difiere |
| Client SAP (public)    | 16 (0x10)              | N/A                   | - |
| Password Medidor 1     | "Contactar soporte"    | "2222222222"          | ✅ Descubierto |
| Timeout                | 180 segundos           | No implementado       | ❌ Falta |
| Keepalive              | Recomendado            | No implementado       | ❌ Falta |
| Buffer cleaning        | Implícito              | Parcial               | ⚠️ Mejorar |
| HDLC framing           | Correcto               | Correcto              | ✅ OK |
| CRC calculation        | Correcto               | Correcto              | ✅ OK |

---

## 13. PENDIENTES Y MEJORAS

### 13.1 Configuración
- [ ] Verificar si Client SAP=1 es específico de este modelo
- [ ] Confirmar password de Medidor 2
- [ ] Determinar dirección física (¿1234 o serial real?)

### 13.2 Implementación
- [ ] Agregar timeout de 180 segundos con keepalive
- [ ] Implementar buffer cleaning agresivo
- [ ] Agregar retry con backoff exponencial
- [ ] Logging detallado de frames

### 13.3 Testing
- [ ] Probar con Client SAP=32 vs SAP=1
- [ ] Probar timeout de inactividad
- [ ] Probar reconexión después de 180s
- [ ] Stress test con múltiples requests

---

## 14. REFERENCIAS

### Documentación Oficial
- **Archivo**: `9.2. Microstar DLMS Protocol Guide.pdf`
- **Páginas clave**: 5-12 (HDLC, Authentication, Timeouts)
- **Apéndices**: A (OBIS codes), B (Interface classes)

### Estándares DLMS/COSEM
- IEC 62056-46: DLMS/COSEM Data Link Layer (HDLC)
- IEC 62056-53: DLMS/COSEM Application Layer
- IEC 62056-61: OBIS Object Identification System

### Implementación en el Proyecto
- `dlms_reader.py`: Cliente DLMS/COSEM con TCP transport
- `dlms_poller_production.py`: Poller con QoS
- `data/admin.db`: Configuración de medidores

---

**Última actualización**: $(date)
**Versión**: 1.0
**Autor**: Análisis del PDF oficial de Microstar
