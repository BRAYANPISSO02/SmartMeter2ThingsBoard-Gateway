# 🏗️ Arquitectura Completa del Sistema DLMS-ThingsBoard

**Sistema de Adquisición de Datos DLMS/COSEM con Telemetría IoT en Tiempo Real**

---

## 📋 Tabla de Contenido

1. [Visión General](#visión-general)
2. [Arquitectura de Alto Nivel](#arquitectura-de-alto-nivel)
3. [Componentes del Sistema](#componentes-del-sistema)
4. [Librerías y Dependencias](#librerías-y-dependencias)
5. [Capa de Protocolo DLMS](#capa-de-protocolo-dlms)
6. [Flujo de Datos](#flujo-de-datos)
7. [Base de Datos](#base-de-datos)
8. [Servicios SystemD](#servicios-systemd)
9. [Patrones de Diseño](#patrones-de-diseño)
10. [Proceso de Enlace de Nuevos Medidores](#proceso-de-enlace-de-nuevos-medidores)

---

## 🎯 Visión General

### Propósito del Sistema

Sistema diseñado para:
- **Lectura continua** de medidores eléctricos DLMS/COSEM vía TCP/IP
- **Publicación en tiempo real** de telemetría a ThingsBoard vía MQTT
- **Gestión multi-medidor** con arquitectura asíncrona y escalable
- **Monitoreo y administración** mediante API REST y dashboard web
- **Alta disponibilidad** con auto-recuperación y circuit breakers

### Características Clave

```
✅ Multi-Meter Concurrent      - Polling paralelo de múltiples medidores
✅ Realtime Telemetry          - Latencia <2s desde medidor a ThingsBoard
✅ Auto-Recovery               - 3 niveles de recuperación automática
✅ Network Monitoring          - Tracking de uso de red (DLMS + MQTT)
✅ Admin Dashboard             - Gestión web con Streamlit
✅ REST API                    - Control programático con FastAPI
✅ Circuit Breaker             - Protección contra reconexiones infinitas
✅ Preventive Reconnection     - Prevención de sesiones DLMS zombie
```

---

## 🏗️ Arquitectura de Alto Nivel

### Diagrama de Capas

```
┌─────────────────────────────────────────────────────────────────┐
│                    CAPA DE PRESENTACIÓN                         │
│  ┌──────────────────────┐  ┌──────────────────────┐           │
│  │ Dashboard Streamlit  │  │   ThingsBoard UI     │           │
│  │  (Puerto 8501)       │  │   (Puerto 8080)      │           │
│  └──────────────────────┘  └──────────────────────┘           │
└────────────────┬────────────────────┬───────────────────────────┘
                 │                    │
┌────────────────▼────────────────────▼───────────────────────────┐
│                  CAPA DE APLICACIÓN                             │
│  ┌──────────────────────┐  ┌──────────────────────┐           │
│  │   Admin API          │  │  ThingsBoard Server  │           │
│  │   FastAPI (8000)     │  │  MQTT Broker (1883)  │           │
│  └──────────────────────┘  └──────────────────────┘           │
└────────────────┬────────────────────┬───────────────────────────┘
                 │                    │
┌────────────────▼────────────────────▼───────────────────────────┐
│                   CAPA DE LÓGICA DE NEGOCIO                     │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  dlms_multi_meter_bridge.py (Proceso Principal)          │  │
│  │  ┌─────────────────────────────────────────────────────┐ │  │
│  │  │ MeterWorker(1)  │ MeterWorker(2)  │ MeterWorker(N) │ │  │
│  │  │ • Async Polling │ • Async Polling │ • Async Polling│ │  │
│  │  │ • MQTT Publish  │ • MQTT Publish  │ • MQTT Publish │ │  │
│  │  │ • Auto-Recovery │ • Auto-Recovery │ • Auto-Recovery│ │  │
│  │  └─────────────────────────────────────────────────────┘ │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────┬───────────────────────────────────────────────┘
                 │
┌────────────────▼───────────────────────────────────────────────┐
│                CAPA DE PROTOCOLO Y TRANSPORTE                  │
│  ┌──────────────────────┐  ┌──────────────────────┐          │
│  │ ProductionDLMSPoller │  │   ThingsBoard MQTT   │          │
│  │ • OptimizedReader    │  │   • QoS 0 (realtime) │          │
│  │ • BufferCleaner      │  │   • Keepalive 60s    │          │
│  │ • Scaler Cache       │  │   • Auto-reconnect   │          │
│  └──────────────────────┘  └──────────────────────┘          │
└────────────────┬───────────────────────────────────────────────┘
                 │
┌────────────────▼───────────────────────────────────────────────┐
│              CAPA DE PROTOCOLO BAJO NIVEL                      │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │ DLMSClient (dlms_reader.py) - Implementación Custom      │ │
│  │ • HDLC Frame Building/Parsing                            │ │
│  │ • CRC16 Calculation                                      │ │
│  │ • SNRM/DISC (Connection Setup/Teardown)                 │ │
│  │ • AARQ/AARE (Application Association)                   │ │
│  │ • GET Request/Response (COSEM Attributes)               │ │
│  │ • Sequence Control (Send/Receive N(S)/N(R))            │ │
│  └──────────────────────────────────────────────────────────┘ │
└────────────────┬───────────────────────────────────────────────┘
                 │
┌────────────────▼───────────────────────────────────────────────┐
│                   CAPA DE TRANSPORTE TCP                       │
│  ┌──────────────────────┐  ┌──────────────────────┐          │
│  │  Socket TCP/IP       │  │  paho.mqtt.client    │          │
│  │  • Timeout 5-7s      │  │  • Protocol: MQTTv311│          │
│  │  • Keepalive         │  │  • Clean Session     │          │
│  │  • Buffer Draining   │  └──────────────────────┘          │
│  └──────────────────────┘                                     │
└────────────────┬───────────────────────────────────────────────┘
                 │
┌────────────────▼───────────────────────────────────────────────┐
│                   CAPA DE HARDWARE                             │
│  ┌──────────────────────┐  ┌──────────────────────┐          │
│  │ Medidores DLMS       │  │  Red Ethernet/WiFi   │          │
│  │ Microstar/ABB/etc    │  │  192.168.1.0/24      │          │
│  │ Puerto TCP 3333      │  └──────────────────────┘          │
│  └──────────────────────┘                                     │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔧 Componentes del Sistema

### 1. **dlms_reader.py** - Cliente DLMS Core

**Descripción:** Implementación minimal y custom del protocolo DLMS/COSEM sobre HDLC/TCP.

**Características:**
- ❌ **NO usa librerías externas** (solo stdlib de Python)
- ✅ Implementación de referencia inspectable
- ✅ Basado en "Microstar DLMS Protocol Guide"
- ✅ Diseñado para extensibilidad

**Responsabilidades:**

```python
class DLMSClient:
    """Cliente DLMS personalizado sin dependencias externas"""
    
    # Construcción de frames HDLC
    def _build_frame(control, dest, src, info) -> bytes:
        """
        Construye frame HDLC con:
        - Format field (0xA000 | length)
        - Dirección destino (server)
        - Dirección origen (client)
        - Control byte (I/U frame)
        - HCS (Header Check Sequence)
        - Info field (DLMS APDU)
        - FCS (Frame Check Sequence)
        """
    
    # Parsing de frames recibidos
    def _parse_frame(frame: bytes) -> ParsedFrame:
        """
        Decodifica frame HDLC:
        - Extrae direcciones
        - Valida HCS/FCS
        - Identifica tipo de frame (SNRM, UA, I)
        - Extrae info field
        """
    
    # Handshake HDLC
    def _hdlc_connect() -> None:
        """
        SNRM (Set Normal Response Mode)
        ← UA (Unnumbered Acknowledgement)
        """
    
    # Asociación DLMS
    def _dlms_associate() -> None:
        """
        AARQ (Application Association Request)
        ← AARE (Application Association Response)
        """
    
    # Lectura de atributos COSEM
    def read_register(obis: str) -> Tuple[value, scaler, unit]:
        """
        GET.request (COSEM Attribute 2 - value)
        ← GET.response (data + scaler + unit)
        
        Aplica scaler: final_value = raw_value * 10^scaler
        """
    
    # Desconexión
    def _hdlc_disconnect() -> None:
        """
        DISC (Disconnect)
        ← UA (Unnumbered Acknowledgement)
        """
```

**Detalles de Implementación:**

```python
# Parámetros de conexión
DLMSClient(
    host='192.168.1.127',          # IP del medidor
    port=3333,                      # Puerto DLMS estándar
    client_sap=1,                   # Service Access Point del cliente
    server_logical=0,               # Logical device del servidor
    server_physical=1,              # Physical device del servidor
    password=b'22222222',           # Password ASCII (8 bytes)
    timeout=5.0,                    # Socket timeout
    max_info_length=None,           # Sin restricción de tamaño
    verbose=False                   # Debug logging
)

# Dirección HDLC combinada
server_address = (logical << 7) | physical
# Ejemplo: logical=0, physical=1 → 0x0001

# Cliente address
client_address = client_sap  # Típicamente 1 o 16
```

**CRC16 HDLC:**
```python
def _crc16_hdlc(data: bytes) -> int:
    """
    Polinomio: x^16 + x^12 + x^5 + 1
    Valor reflejado: 0x8408
    Inicial: 0xFFFF
    Final: ~crc & 0xFFFF
    
    Transmisión: LSB primero
    """
    crc = 0xFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 0x0001:
                crc = (crc >> 1) ^ 0x8408
            else:
                crc >>= 1
    return (~crc) & 0xFFFF
```

**Códigos OBIS Soportados:**
```python
OBIS_CODES = {
    "1-1:32.7.0": "Voltage L1 (V)",
    "1-1:52.7.0": "Voltage L2 (V)",
    "1-1:72.7.0": "Voltage L3 (V)",
    "1-1:31.7.0": "Current L1 (A)",
    "1-1:51.7.0": "Current L2 (A)",
    "1-1:71.7.0": "Current L3 (A)",
    "1-1:14.7.0": "Frequency (Hz)",
    "1-1:1.7.0": "Active Power Total (W)",
    "1-1:1.8.0": "Active Energy Import (Wh)",
    "1-1:2.8.0": "Active Energy Export (Wh)",
}
```

---

### 2. **dlms_poller_production.py** - Poller Robusto

**Descripción:** Sistema de polling optimizado con auto-recuperación.

**Características:**
- ✅ Caché de scalers (reduce latencia 50%)
- ✅ Circuit breaker integrado
- ✅ Buffer cleaner automático
- ✅ Métricas de rendimiento

**Arquitectura:**

```python
class ProductionDLMSPoller:
    """
    Poller optimizado que combina:
    - OriginalDLMSClient (conexión HDLC/DLMS)
    - OptimizedDLMSReader (caché de scalers)
    - BufferCleaner (limpieza TCP)
    """
    
    def __init__(self):
        self.config = DLMSConfig(
            timeout=7.0,                    # Timeout tolerante
            max_retries=3,                  # Reintentos por lectura
            retry_delay=3.0,                # Backoff entre reintentos
            reconnect_threshold=15,         # Errores antes de reconectar
            circuit_breaker_threshold=15,   # Errores para abrir circuito
            circuit_breaker_timeout=30.0,   # Tiempo con circuito abierto
            buffer_clear_on_error=True      # Limpiar buffer al error
        )
```

**Optimizaciones Implementadas:**

1. **Scaler Caching (Fase 2):**
```python
class OptimizedDLMSReader:
    """
    Primera lectura:  GET value + scaler + unit  (~400ms)
    Lecturas posteriores:  GET value only  (~200ms)
    
    Mejora: 50% reducción en latencia
    """
    
    def __init__(self, client, use_batch=False):
        self.scaler_cache = {}  # {obis: (scaler, unit)}
        self.use_batch = use_batch
    
    def read_optimized(self, obis: str):
        if obis in self.scaler_cache:
            # Solo leer value (Attribute 2)
            raw_value = self.client.read_attribute(obis, attr=2)
            scaler, unit = self.scaler_cache[obis]
            return raw_value * (10 ** scaler), unit
        else:
            # Primera lectura: value + scaler + unit
            result = self.client.read_register(obis)
            self.scaler_cache[obis] = (result[1], result[2])
            return result[0], result[2]
```

2. **Buffer Cleaning:**
```python
class BufferCleaner:
    """
    Previene errores "Invalid HDLC frame boundary"
    limpiando basura del buffer TCP.
    """
    
    def aggressive_drain(socket):
        """Drena todo el buffer disponible"""
        socket.setblocking(False)
        try:
            while socket.recv(4096):
                pass
        except BlockingIOError:
            pass
        socket.setblocking(True)
    
    def find_frame_start(socket):
        """Busca el flag 0x7E de inicio de frame"""
        while True:
            byte = socket.recv(1)
            if byte[0] == 0x7E:
                return byte
```

3. **Preventive Reconnection (Reciente):**
```python
# En dlms_to_mosquitto_bridge.py
MAX_READS_BEFORE_RECONNECT = 10  # ~30s con interval=2s

if reads_since_reconnect >= MAX_READS_BEFORE_RECONNECT:
    logger.info("🔄 Reconexión preventiva")
    client.close()
    time.sleep(1.0)  # Limpiar socket
    client.connect()  # Con 5 reintentos
    reads_since_reconnect = 0
```

---

### 3. **dlms_multi_meter_bridge.py** - Orquestador Multi-Medidor

**Descripción:** Servicio principal que maneja múltiples medidores concurrentemente.

**Arquitectura Asíncrona:**

```python
class MultiMeterBridge:
    """
    Orquestador que gestiona N workers en paralelo.
    Cada worker es independiente con su propio:
    - DLMS Client
    - MQTT Connection (compartida)
    - Thread de ejecución
    """
    
    def __init__(self):
        # Configuración MQTT compartida (1 conexión)
        self.mqtt_client = mqtt.Client(
            client_id=f"dlms_multi_meter_bridge_{id(self)}",
            clean_session=True,
            protocol=mqtt.MQTTv311
        )
        
        # Workers por medidor
        self.workers = []
        
    def start(self):
        # Cargar medidores desde DB
        meters = self.load_meters_from_db()
        
        # Crear worker por medidor
        for meter in meters:
            worker = MeterWorker(meter, self.mqtt_client)
            self.workers.append(worker)
            worker.start()  # Thread.start()
        
        # Monitoreo cada 60s
        while True:
            self.report_system_status()
            time.sleep(60)
```

**MeterWorker:**

```python
class MeterWorker(threading.Thread):
    """Worker independiente para un medidor"""
    
    def __init__(self, meter_config, mqtt_client):
        super().__init__(daemon=True)
        self.meter = meter_config
        self.mqtt_client = mqtt_client
        self.poller = ProductionDLMSPoller(
            host=meter.ip_address,
            port=meter.port,
            interval=2.0  # 2 segundos entre lecturas
        )
        
    def run(self):
        """Loop principal del worker"""
        self.poller.connect()
        
        while self.running:
            try:
                # Leer mediciones
                data = self.poller.poll()
                
                # Publicar a ThingsBoard
                if data:
                    self.mqtt_client.publish(
                        topic="v1/devices/me/telemetry",
                        payload=json.dumps(data),
                        qos=0  # Fire-and-forget para realtime
                    )
                
                # Esperar intervalo
                time.sleep(2.0)
                
            except Exception as e:
                self.handle_error(e)
```

**Sistema de Auto-Recuperación (3 Niveles):**

```python
# Nivel 1: Retry en lectura individual
try:
    value = client.read_register(obis)
except HDLCError:
    time.sleep(0.1)
    value = client.read_register(obis)  # Segundo intento

# Nivel 2: Reconexión DLMS
if consecutive_errors >= 5:
    client.disconnect()
    time.sleep(1.0)
    client.connect()

# Nivel 3: Circuit Breaker
if reconnections_per_hour >= 15:
    logger.error("Circuit breaker OPEN")
    time.sleep(30.0)  # Pausa larga
    # Reintentar después
```

---

### 4. **admin/database.py** - Capa de Persistencia

**ORM:** SQLAlchemy con SQLite

**Modelos de Datos:**

```python
# Tabla: meters
class Meter(Base):
    id: int                     # PK
    name: str                   # Nombre único
    ip_address: str             # IP del medidor
    port: int                   # Puerto DLMS (default: 3333)
    client_id: int              # DLMS client SAP
    server_id: int              # DLMS server physical
    
    # Estado
    status: str                 # 'active' | 'inactive' | 'error'
    last_seen: datetime         # Última lectura exitosa
    last_error: str             # Último error
    error_count: int            # Contador de errores
    
    # ThingsBoard
    tb_enabled: bool            # Habilitar publicación
    tb_host: str                # MQTT broker
    tb_port: int                # Puerto MQTT (1883)
    tb_token: str               # Token de dispositivo
    tb_device_name: str         # Nombre en ThingsBoard
    
    # Metadata
    model: str                  # Modelo del medidor
    serial_number: str          # Serial
    firmware_version: str       # Versión FW
    
    # Timestamps
    created_at: datetime
    updated_at: datetime

# Tabla: meter_configs
class MeterConfig(Base):
    id: int
    meter_id: int               # FK a meters
    measurement_name: str       # 'voltage_l1'
    obis_code: str              # '1-1:32.7.0'
    enabled: bool               # Activar medición
    sampling_interval: float    # Segundos entre lecturas
    tb_key: str                 # Key en ThingsBoard

# Tabla: meter_metrics
class MeterMetric(Base):
    id: int
    meter_id: int
    timestamp: datetime
    
    # Performance
    avg_read_time: float        # Tiempo promedio de lectura
    min_read_time: float
    max_read_time: float
    
    # Success rate
    total_reads: int
    successful_reads: int
    failed_reads: int
    success_rate: float         # Porcentaje
    
    # MQTT
    messages_sent: int
    messages_buffered: int
    mqtt_reconnections: int
    
    # Cache (Fase 2)
    cache_hits: int
    cache_misses: int
    cache_hit_rate: float

# Tabla: network_metrics
class NetworkMetric(Base):
    id: int
    meter_id: int
    timestamp: datetime
    
    # DLMS
    dlms_requests_sent: int
    dlms_responses_recv: int
    dlms_bytes_sent: int
    dlms_bytes_recv: int
    
    # MQTT
    mqtt_messages_sent: int
    mqtt_bytes_sent: int
    
    # Bandwidth
    bandwidth_tx_bps: float     # Bytes/segundo TX
    bandwidth_rx_bps: float     # Bytes/segundo RX

# Tabla: alarms
class Alarm(Base):
    id: int
    meter_id: int
    severity: str               # 'critical' | 'warning' | 'info'
    category: str               # 'connection' | 'performance'
    message: str                # Descripción
    acknowledged: bool          # Reconocida por operador
    timestamp: datetime
```

**Funciones de Acceso:**

```python
def create_meter(session, name, ip_address, port, tb_token):
    """Crea un nuevo medidor en la BD"""
    meter = Meter(
        name=name,
        ip_address=ip_address,
        port=port,
        tb_token=tb_token,
        status='inactive'
    )
    session.add(meter)
    session.commit()
    return meter

def get_active_meters(session):
    """Obtiene medidores activos para polling"""
    return session.query(Meter).filter(
        Meter.status == 'active',
        Meter.tb_enabled == True
    ).all()

def record_metrics(session, meter_id, metrics_dict):
    """Registra métricas de performance"""
    metric = MeterMetric(
        meter_id=meter_id,
        **metrics_dict
    )
    session.add(metric)
    session.commit()
```

---

### 5. **admin/api.py** - API REST

**Framework:** FastAPI

**Endpoints:**

```python
# Medidores
GET    /api/meters              # Listar todos
GET    /api/meters/{id}         # Detalle
POST   /api/meters              # Crear nuevo
PUT    /api/meters/{id}         # Actualizar
DELETE /api/meters/{id}         # Eliminar

# Estado del sistema
GET    /api/system/health       # Health check
GET    /api/system/status       # Estado de services

# Métricas
GET    /api/metrics/{meter_id}  # Métricas de un medidor
GET    /api/network/metrics     # Métricas de red

# Alarmas
GET    /api/alarms              # Listar alarmas
POST   /api/alarms/{id}/ack     # Reconocer alarma

# Configuración
GET    /api/config/{meter_id}   # Configuración
PUT    /api/config/{meter_id}   # Actualizar config
```

**Ejemplo de Uso:**

```bash
# Crear medidor
curl -X POST http://localhost:8000/api/meters \
  -H "Content-Type: application/json" \
  -d '{
    "name": "medidor_planta_A",
    "ip_address": "192.168.1.150",
    "port": 3333,
    "tb_token": "YOUR_TB_TOKEN_HERE",
    "measurements": ["voltage_l1", "current_l1", "active_power"]
  }'

# Obtener métricas
curl http://localhost:8000/api/metrics/1

# Respuesta:
{
  "meter_id": 1,
  "avg_read_time": 1.35,
  "success_rate": 98.5,
  "messages_sent": 1523,
  "cache_hit_rate": 95.2
}
```

---

### 6. **admin/dashboard.py** - Dashboard Web

**Framework:** Streamlit

**Funcionalidades:**

```python
import streamlit as st

# Página principal
st.title("DLMS Multi-Meter Monitor")

# Sección 1: Estado de medidores
st.header("Estado de Medidores")
meters = get_active_meters()
for meter in meters:
    col1, col2, col3 = st.columns(3)
    col1.metric("Nombre", meter.name)
    col2.metric("Success Rate", f"{meter.success_rate}%")
    col3.metric("Última lectura", meter.last_seen)

# Sección 2: Gráficas de rendimiento
st.header("Rendimiento")
metrics = get_recent_metrics(hours=24)
st.line_chart(metrics['success_rate'])

# Sección 3: Alarmas activas
st.header("Alarmas")
alarms = get_unacknowledged_alarms()
for alarm in alarms:
    st.error(f"{alarm.severity}: {alarm.message}")
    if st.button(f"Reconocer #{alarm.id}"):
        acknowledge_alarm(alarm.id)

# Sección 4: Agregar medidor
st.header("Agregar Nuevo Medidor")
with st.form("add_meter"):
    name = st.text_input("Nombre")
    ip = st.text_input("IP Address")
    port = st.number_input("Puerto", value=3333)
    token = st.text_input("ThingsBoard Token")
    
    if st.form_submit_button("Crear"):
        create_meter(name, ip, port, token)
        st.success("Medidor creado!")
```

---

## 📦 Librerías y Dependencias

### Dependencias Core (requirements.txt)

```plaintext
# DLMS/COSEM Protocol
dlms-cosem==22.3.0
  ⚠️ IMPORTANTE: Instalada pero NO USADA en producción
  📝 Solo para referencia y testing
  ✅ Implementación custom en dlms_reader.py

# MQTT - ThingsBoard Official SDK
tb-mqtt-client>=1.13.0
  ✅ Cliente oficial de ThingsBoard
  ✅ Manejo automático de reconexión
  ✅ Compresión de payloads

tb-paho-mqtt-client>=2.1.2
  ✅ Backend MQTT (fork de paho)
  ✅ Compatible con MQTTv311
  ✅ SSL/TLS support

# Database ORM
sqlalchemy>=2.0.0
  ✅ ORM para SQLite
  ✅ Migrations automáticas
  ✅ Relaciones declarativas

# Network Monitoring
psutil>=5.9.0
  ✅ Métricas de CPU/memoria
  ✅ Network I/O stats
  ✅ Process management

# Utilities
python-dateutil>=2.8.0
  ✅ Timezone handling
  ✅ Date parsing

requests>=2.31.0
  ✅ HTTP client para APIs
  ✅ ThingsBoard REST API
```

### Dependencias Admin (requirements-admin.txt)

```plaintext
# API Framework
fastapi>=0.104.0
  ✅ REST API framework
  ✅ Auto-generated docs (Swagger)
  ✅ Async support

uvicorn[standard]>=0.24.0
  ✅ ASGI server
  ✅ Auto-reload en desarrollo

# Dashboard
streamlit>=1.28.0
  ✅ Web dashboard framework
  ✅ Reactive components
  ✅ Data visualization

# Data Processing
pandas>=2.1.0
  ✅ DataFrames para métricas
  ✅ Time-series analysis

plotly>=5.17.0
  ✅ Interactive charts
  ✅ Real-time updates
```

### ¿Por qué NO se usa dlms-cosem?

**Razones técnicas:**

1. **Sobre-ingeniería:** dlms-cosem es completo pero complejo (10,000+ líneas)
2. **Falta de control:** Difícil debuggear errores HDLC internos
3. **Performance:** Overhead innecesario para caso de uso simple
4. **Customización:** Necesitábamos buffer cleaning y optimizaciones específicas

**Nuestra implementación custom:**

```python
# dlms_reader.py - 839 líneas
✅ Minimal y auditable
✅ Basado en documentación del fabricante
✅ Optimizado para Microstar
✅ Fácil de extender
✅ Sin dependencias externas
✅ Control total sobre HDLC/buffer

# Funcionalidad suficiente
✓ SNRM/DISC (connection)
✓ AARQ/AARE (association)
✓ GET.request/response (reading)
✓ CRC16 HDLC
✓ Address encoding/decoding
✓ Frame building/parsing
```

**Cuándo usar dlms-cosem:**

- Medidores con features avanzadas (SET, ACTION)
- Security alta (GMAC, encryption)
- Múltiples fabricantes
- Implementación rápida (prototipo)

**Cuándo usar custom (nuestro caso):**

- Medidores específicos (Microstar)
- Performance crítico
- Debugging profundo necesario
- Optimizaciones específicas

---

## 🔄 Flujo de Datos Completo

### Lectura de Medidor → ThingsBoard

```
┌─────────────────────────────────────────────────────────────────┐
│ FASE 1: Conexión DLMS (Ocurre 1 vez al inicio)                 │
└─────────────────────────────────────────────────────────────────┘

1. TCP Connect
   MeterWorker → Socket TCP → Medidor:3333
   Timeout: 5s

2. HDLC Connection
   Client → SNRM frame → Medidor
   ← UA frame ← Medidor
   Estado: HDLC Connected

3. DLMS Association
   Client → AARQ frame → Medidor
   ← AARE frame ← Medidor
   Estado: DLMS Associated

┌─────────────────────────────────────────────────────────────────┐
│ FASE 2: Polling Loop (Cada 2 segundos)                         │
└─────────────────────────────────────────────────────────────────┘

4. Leer Mediciones (secuencial)
   Para cada OBIS code:
   
   4a. GET Request
       Client → GET(obis, attr=2) → Medidor
       Frame: I-frame con N(S), N(R)
   
   4b. GET Response
       ← Data(value, scaler, unit) ← Medidor
       Parsing: Extraer value + scaler + unit
   
   4c. Aplicar Scaler
       final_value = raw_value * 10^scaler
       Ejemplo: 1365 * 10^(-1) = 136.5 V

5. Construir Telemetry Payload
   data = {
       "voltage_l1": 136.5,
       "current_l1": 1.34,
       "frequency": 59.97,
       "active_power": 0.60,
       "active_energy": 56352.0,
       "ts": 1730745600000  # Unix timestamp ms
   }

6. Publicar a MQTT
   mqtt_client.publish(
       topic="v1/devices/me/telemetry",
       payload=json.dumps(data),
       qos=0
   )

7. Esperar Intervalo
   time.sleep(2.0)

┌─────────────────────────────────────────────────────────────────┐
│ FASE 3: ThingsBoard Processing                                 │
└─────────────────────────────────────────────────────────────────┘

8. MQTT Broker recibe mensaje
   - Valida token de dispositivo
   - Enruta a Rule Engine

9. Rule Engine procesa
   - Guarda en time-series DB (Cassandra/PostgreSQL)
   - Evalúa alarmas (thresholds)
   - Activa visualización en dashboard

10. Dashboard actualiza
    - Gráficas en tiempo real
    - Widgets de valores actuales
    - Indicadores de estado

┌─────────────────────────────────────────────────────────────────┐
│ FASE 4: Manejo de Errores                                      │
└─────────────────────────────────────────────────────────────────┘

Error HDLC:
   - Retry inmediato (0.1s)
   - Buffer clean
   - Segundo intento

Error persistente (5 fallos):
   - Cerrar conexión HDLC
   - Esperar 1s
   - Reconectar desde FASE 1

Circuit Breaker (15 reconexiones/hora):
   - Abrir circuito
   - Pausa 30s
   - Reintentar
```

### Timing y Latencias

```
Operación                           Tiempo típico
──────────────────────────────────────────────────
TCP Connect                         50-100ms
SNRM → UA                           100-150ms
AARQ → AARE                         150-200ms
GET Request → Response              200-400ms
  (con caché de scaler)             100-200ms
Aplicar scaler                      <1ms
JSON serialize                      <1ms
MQTT publish                        10-50ms
ThingsBoard processing              50-100ms
──────────────────────────────────────────────────
Total (lectura → dashboard):        1.0-2.0s
```

---

## 🛠️ Servicios SystemD

### dlms-mosquitto-bridge.service

**Archivo:** `/etc/systemd/system/dlms-mosquitto-bridge.service`

```ini
[Unit]
Description=DLMS to Mosquitto Bridge
After=network.target mosquitto.service
Wants=mosquitto.service

[Service]
Type=simple
User=pci
WorkingDirectory=/home/pci/Documents/sebas_giraldo/Tesis-app/dlms-bridge
Environment="PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
ExecStart=/home/pci/Documents/sebas_giraldo/Tesis-app/dlms-bridge/venv/bin/python3 \
          dlms_to_mosquitto_bridge.py --meter-id 1 --interval 2.0

# Restart policy
Restart=always
RestartSec=10s

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=dlms-bridge

[Install]
WantedBy=multi-user.target
```

**Comandos:**

```bash
# Habilitar al inicio
sudo systemctl enable dlms-mosquitto-bridge.service

# Iniciar
sudo systemctl start dlms-mosquitto-bridge.service

# Ver estado
sudo systemctl status dlms-mosquitto-bridge.service

# Ver logs
sudo journalctl -u dlms-mosquitto-bridge.service -f

# Reiniciar
sudo systemctl restart dlms-mosquitto-bridge.service
```

### qos-supervisor.service

**Descripción:** Supervisor de calidad de servicio que monitorea y recupera automáticamente.

```ini
[Unit]
Description=QoS Supervisor for DLMS Bridge
After=network.target dlms-mosquitto-bridge.service

[Service]
Type=simple
User=pci
Environment="PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
ExecStart=/home/pci/.../venv/bin/python3 qos_supervisor_service.py

# Restart policy
Restart=always
RestartSec=5s

[Install]
WantedBy=multi-user.target
```

**Funcionalidades:**

```python
class QoSSupervisor:
    """
    Monitorea cada 10s:
    - Timestamp de telemetría (debe cambiar)
    - Estado del servicio bridge
    - Estado del gateway TB
    
    Acciones correctivas:
    - Restart bridge si telemetría stale
    - Restart gateway si no conecta
    - Registra métricas en BD
    """
    
    CHECK_INTERVAL = 10        # 10 segundos entre checks
    TELEMETRY_MAX_AGE = 20     # 20 segundos máximo sin datos
    REST_DURATION = 120        # 2 minutos de descanso cada ciclo
```

---

## 🎨 Patrones de Diseño

### 1. **Worker Thread Pattern**

Cada medidor tiene su propio thread independiente.

```python
# Ventajas:
✅ Aislamiento (fallo en un medidor no afecta otros)
✅ Concurrencia (polling paralelo)
✅ Escalabilidad (N threads para N medidores)

# Implementación:
class MeterWorker(threading.Thread):
    def run(self):
        while self.running:
            self.poll_and_publish()
```

### 2. **Circuit Breaker Pattern**

Previene reconexiones infinitas.

```python
class CircuitBreaker:
    CLOSED → OPEN (15 fallos)
    OPEN → HALF_OPEN (30s después)
    HALF_OPEN → CLOSED (1 éxito) o OPEN (1 fallo)
```

### 3. **Repository Pattern**

Abstracción de acceso a datos.

```python
class MeterRepository:
    def get_all_active(self):
        return session.query(Meter).filter(...)
    
    def update_status(self, meter_id, status):
        meter = session.query(Meter).get(meter_id)
        meter.status = status
        session.commit()
```

### 4. **Factory Pattern**

Creación de clientes DLMS.

```python
def create_dlms_client(meter_config):
    return DLMSClient(
        host=meter_config.ip_address,
        port=meter_config.port,
        ...
    )
```

### 5. **Observer Pattern**

Sistema de alarmas.

```python
class AlarmObserver:
    def on_low_success_rate(self, meter_id, rate):
        alarm = Alarm(
            meter_id=meter_id,
            severity='warning',
            message=f'Success rate bajo: {rate}%'
        )
        db.add(alarm)
```

---

## 🔗 Proceso de Enlace de Nuevos Medidores

### Opción 1: Via Dashboard (Recomendado)

```
1. Abrir Dashboard
   http://localhost:8501

2. Ir a sección "Agregar Medidor"

3. Completar formulario:
   ┌──────────────────────────────────────┐
   │ Nombre: medidor_planta_B             │
   │ IP: 192.168.1.150                    │
   │ Puerto: 3333                         │
   │ ThingsBoard Token: YOUR_TOKEN        │
   │ Mediciones:                          │
   │   ☑ voltage_l1                       │
   │   ☑ current_l1                       │
   │   ☑ active_power                     │
   └──────────────────────────────────────┘

4. Clic "Crear Medidor"

5. Dashboard confirma creación

6. Reiniciar servicio:
   sudo systemctl restart dlms-mosquitto-bridge.service

7. Verificar en ThingsBoard:
   - Ir a Devices
   - Buscar "medidor_planta_B"
   - Ver telemetría en tiempo real
```

### Opción 2: Via API REST

```bash
# 1. Crear dispositivo en ThingsBoard
curl -X POST http://localhost:8080/api/device \
  -H "X-Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "medidor_planta_B",
    "type": "DLMS_METER"
  }'

# Respuesta incluye: device.id y credentialsId

# 2. Obtener token del dispositivo
curl http://localhost:8080/api/device/$DEVICE_ID/credentials \
  -H "X-Authorization: Bearer $JWT_TOKEN"

# Respuesta: {"credentialsId": "...", "credentialsType": "ACCESS_TOKEN", "credentialsValue": "YOUR_TOKEN"}

# 3. Agregar medidor a nuestra BD
curl -X POST http://localhost:8000/api/meters \
  -H "Content-Type: application/json" \
  -d '{
    "name": "medidor_planta_B",
    "ip_address": "192.168.1.150",
    "port": 3333,
    "tb_token": "YOUR_TOKEN",
    "tb_device_name": "medidor_planta_B",
    "measurements": ["voltage_l1", "current_l1", "active_power"]
  }'

# 4. Reiniciar servicio
sudo systemctl restart dlms-mosquitto-bridge.service

# 5. Verificar funcionamiento
curl http://localhost:8000/api/meters/2
```

### Opción 3: Via Python Script

```python
#!/usr/bin/env python3
"""Script para agregar medidor programáticamente"""

from admin.database import Database, create_meter
from sqlalchemy.orm import Session

def add_meter(
    name: str,
    ip_address: str,
    port: int,
    tb_token: str,
    measurements: list
):
    """Agrega un nuevo medidor a la base de datos"""
    
    # 1. Conectar a DB
    db = Database('data/admin.db')
    session = db.get_session()
    
    # 2. Crear medidor
    meter = create_meter(
        session=session,
        name=name,
        ip_address=ip_address,
        port=port,
        tb_token=tb_token
    )
    
    # 3. Agregar configuraciones de mediciones
    for measurement in measurements:
        obis = MEASUREMENTS[measurement][0]
        config = MeterConfig(
            meter_id=meter.id,
            measurement_name=measurement,
            obis_code=obis,
            enabled=True,
            sampling_interval=2.0
        )
        session.add(config)
    
    session.commit()
    session.close()
    
    print(f"✅ Medidor '{name}' agregado con ID {meter.id}")
    print(f"   Reiniciar servicio: sudo systemctl restart dlms-mosquitto-bridge.service")

# Uso
if __name__ == "__main__":
    add_meter(
        name="medidor_planta_B",
        ip_address="192.168.1.150",
        port=3333,
        tb_token="YOUR_THINGSBOARD_TOKEN",
        measurements=["voltage_l1", "current_l1", "active_power", "frequency"]
    )
```

### Verificación Post-Enlace

```bash
# 1. Ver logs del servicio
sudo journalctl -u dlms-mosquitto-bridge.service -f

# Debe mostrar:
# "✅ DLMS conectado"
# "📤 VOL: 136.5 | CUR: 1.34 | ..."

# 2. Verificar en ThingsBoard
# http://localhost:8080/devices
# Buscar dispositivo → Ver telemetría

# 3. Verificar métricas en API
curl http://localhost:8000/api/metrics/2

# 4. Ver en dashboard
# http://localhost:8501
# Debe aparecer el nuevo medidor con estado "active"
```

---

## 📊 Conclusión

Este sistema implementa una arquitectura completa para adquisición de datos DLMS/COSEM con:

**Fortalezas:**
- ✅ Implementación custom DLMS sin dependencias externas
- ✅ Alta performance con optimizaciones específicas
- ✅ Arquitectura escalable multi-medidor
- ✅ Auto-recuperación en 3 niveles
- ✅ Monitoreo completo (métricas, alarmas, logs)
- ✅ APIs REST y Dashboard web
- ✅ Integración nativa con ThingsBoard

**Decisiones Técnicas Clave:**
1. **No usar dlms-cosem:** Implementación custom para control total y performance
2. **Caché de scalers:** Reducción 50% en latencia
3. **Buffer cleaning agresivo:** Solución a errores HDLC
4. **Reconexión preventiva:** Prevención de sesiones zombie
5. **Circuit breaker:** Protección contra reconexiones infinitas

**Próximos Pasos:**
- Implementar batch reading (leer múltiples OBIS en 1 request)
- Agregar soporte para SET operations
- Implementar encryption (GMAC)
- Dashboard de analíticas avanzadas
- Soporte para más fabricantes

---

**Autor:** Sistema DLMS-ThingsBoard  
**Fecha:** Noviembre 2025  
**Versión:** 2.3
