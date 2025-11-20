# Sistema de Telemetría IoT para Medidores Eléctricos DLMS/COSEM

**Proyecto de Grado** - Ingeniería Electrónica  
**Autor:** Brayan Ricardo Pisso Ramírez  
**Director:** [Nombre del Director de Tesis]  
**Universidad:** Universidad Nacional de Colombia - Sede Manizales  
**Año:** 2025

---

## 📄 Resumen Ejecutivo

Este proyecto implementa un **sistema de telemetría IoT** para la adquisición, transmisión y almacenamiento de datos eléctricos en tiempo real desde medidores inteligentes que implementan el protocolo **DLMS/COSEM** (Device Language Message Specification/Companion Specification for Energy Metering). 

El sistema permite monitorear de forma remota y continua variables eléctricas como voltaje, corriente, frecuencia, potencia activa y energía consumida, enviando los datos a la plataforma **ThingsBoard IoT** para su visualización, análisis histórico y generación de alarmas.

### Características Principales

- ✅ **Lectura automática** de medidores DLMS/COSEM vía TCP/IP
- ✅ **Multi-medidor concurrente** - Gestión simultánea de múltiples dispositivos
- ✅ **Auto-recuperación** - Sistema robusto con 3 niveles de recuperación ante fallos
- ✅ **Publicación MQTT** - Transmisión de datos con QoS nivel 1 (garantía de entrega)
- ✅ **Almacenamiento local** - Base de datos SQLite para configuración y métricas
- ✅ **Monitoreo en tiempo real** - Detección de fallos y generación de alarmas
- ✅ **Escalabilidad** - Arquitectura modular para añadir medidores sin modificar código

### Alcance del Sistema

**Lo que incluye este proyecto:**
- Módulo de lectura DLMS/COSEM (`dlms_multi_meter_bridge.py`)
- Cliente MQTT optimizado para ThingsBoard
- Base de datos SQLite para gestión de configuración
- Sistema de auto-recuperación y monitoreo
- CLI de gestión de medidores
- API REST opcional para administración

**Componentes externos requeridos:**
- Medidores eléctricos con soporte DLMS/COSEM y conectividad TCP/IP
- Plataforma ThingsBoard IoT (instalación separada)
- Broker MQTT Mosquitto (opcional, solo para arquitectura Gateway)

### Limitaciones

- Compatible únicamente con protocolo DLMS/COSEM (no Modbus RTU/TCP, IEC 61850)
- Requiere medidores con conectividad Ethernet/TCP-IP (no RS485 serial directo)
- Diseñado específicamente para ThingsBoard (no soporta otras plataformas IoT)

---

## 🏗️ Arquitectura del Sistema

### Diagrama de Bloques

```
┌──────────────────────────────────────────────────────────────────┐
│                     CAPA FÍSICA - MEDIDORES                      │
│                                                                  │
│  ┌──────────────────┐           ┌──────────────────┐           │
│  │  Medidor DLMS #1 │           │  Medidor DLMS #2 │           │
│  │  IP: 192.168.x.x │           │  IP: 192.168.x.x │           │
│  │  Puerto: 3333    │           │  Puerto: 3333    │           │
│  │                  │           │                  │           │
│  │  Variables:      │           │  Variables:      │           │
│  │  • Voltaje (V)   │           │  • Voltaje (V)   │           │
│  │  • Corriente (A) │           │  • Corriente (A) │           │
│  │  • Frecuencia    │           │  • Frecuencia    │           │
│  │  • Potencia (W)  │           │  • Potencia (W)  │           │
│  │  • Energía (Wh)  │           │  • Energía (Wh)  │           │
│  └────────┬─────────┘           └────────┬─────────┘           │
│           │                              │                      │
└───────────┼──────────────────────────────┼──────────────────────┘
            │                              │
            │    Protocolo DLMS/COSEM      │
            │    sobre TCP/IP (puerto 3333)│
            │                              │
┌───────────▼──────────────────────────────▼──────────────────────┐
│              CAPA DE APLICACIÓN - PYTHON                         │
│                                                                  │
│  ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓  │
│  ┃  dlms_multi_meter_bridge.py                              ┃  │
│  ┃  (SCRIPT PRINCIPAL - Orquestador)                        ┃  │
│  ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛  │
│                                                                  │
│  ┌────────────────────┐          ┌────────────────────┐        │
│  │  MeterWorker #1    │          │  MeterWorker #2    │        │
│  │  ┌──────────────┐  │          │  ┌──────────────┐  │        │
│  │  │ DLMS Poller  │  │          │  │ DLMS Poller  │  │        │
│  │  │ - Conexión   │  │          │  │ - Conexión   │  │        │
│  │  │ - Lectura    │  │          │  │ - Lectura    │  │        │
│  │  │ - Parseo     │  │          │  │ - Parseo     │  │        │
│  │  └──────┬───────┘  │          │  └──────┬───────┘  │        │
│  │         │          │          │         │          │        │
│  │  ┌──────▼───────┐  │          │  ┌──────▼───────┐  │        │
│  │  │ MQTT Client  │  │          │  │ MQTT Client  │  │        │
│  │  │ - Formateo   │  │          │  │ - Formateo   │  │        │
│  │  │ - Publicación│  │          │  │ - Publicación│  │        │
│  │  │ - QoS=1      │  │          │  │ - QoS=1      │  │        │
│  │  └──────┬───────┘  │          │  └──────┬───────┘  │        │
│  └─────────┼──────────┘          └─────────┼──────────┘        │
│            │                               │                   │
│            └───────────────┬───────────────┘                   │
│                            │                                   │
│                  ┌─────────▼─────────┐                         │
│                  │  admin/database.py│                         │
│                  │  SQLite Database  │                         │
│                  │  • Configuración  │                         │
│                  │  • Métricas       │                         │
│                  │  • Alarmas        │                         │
│                  └───────────────────┘                         │
│                                                                  │
└──────────────────────────┬───────────────────────────────────────┘
                           │
                           │ MQTT Protocol
                           │ (QoS=1, JSON payload)
                           │
┌──────────────────────────▼───────────────────────────────────────┐
│                  PLATAFORMA IoT - ThingsBoard                    │
│                  (Instalación Externa)                           │
│                                                                  │
│  • Recepción de telemetría vía MQTT                             │
│  • Almacenamiento en base de datos time-series                  │
│  • Dashboards de visualización en tiempo real                   │
│  • Generación de alarmas y notificaciones                       │
│  • Análisis histórico de datos                                  │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### Componentes del Sistema

#### 1. **dlms_multi_meter_bridge.py** (Script Principal)
**Función:** Orquestador principal que gestiona múltiples medidores de forma concurrente.

**Responsabilidades:**
- Lectura de configuración desde base de datos SQLite
- Creación de workers independientes (uno por medidor)
- Ejecución asíncrona de múltiples workers en paralelo
- Monitoreo de salud del sistema
- Gestión del ciclo de vida de conexiones

**Características técnicas:**
- Programación asíncrona con `asyncio`
- Arquitectura multi-threading para escalabilidad
- Sistema de auto-recuperación de 3 niveles
- Logging estructurado con niveles INFO/WARNING/ERROR

#### 2. **dlms_poller_production.py** (Lector DLMS)
**Función:** Cliente optimizado para comunicación con medidores DLMS/COSEM.

**Características:**
- Implementación completa del protocolo DLMS/COSEM
- Soporte para HDLC (High-Level Data Link Control) sobre TCP/IP
- Lectura de códigos OBIS (Object Identification System)
- Manejo robusto de errores de comunicación
- Timeouts configurables y reintentos automáticos
- Caché de scalers para optimización de velocidad

#### 3. **tb_mqtt_client.py** (Cliente MQTT)
**Función:** Wrapper optimizado de paho-mqtt para ThingsBoard.

**Características:**
- Conexión persistente con keepalive
- QoS nivel 1 (at-least-once delivery)
- Formateo automático de telemetría para ThingsBoard
- Reconexión automática ante pérdida de conexión
- Client ID único para evitar conflictos
- Callbacks para monitoreo de estado

#### 4. **admin/database.py** (Gestión de Datos)
**Función:** Capa de acceso a datos con SQLAlchemy ORM.

**Tablas principales:**
- `meters`: Configuración de medidores (IP, puerto, credenciales)
- `metrics`: Historial de mediciones
- `alarms`: Registro de eventos y alertas
- `dlms_diagnostics`: Diagnósticos de comunicación DLMS

#### 5. **meter_cli.py** (Interfaz de Línea de Comandos)
**Función:** Herramienta CLI para gestión manual de medidores.

**Comandos disponibles:**
```bash
meter_cli.py list              # Listar medidores configurados
meter_cli.py status <id>       # Ver estado detallado de un medidor
meter_cli.py test <id>         # Probar conectividad TCP
meter_cli.py follow <id>       # Seguir logs en tiempo real
```

---

## 📦 Requisitos del Sistema

### Hardware

| Componente | Especificación Mínima | Recomendado |
|------------|----------------------|-------------|
| Procesador | Intel/AMD x64 o ARM  | Multi-core  |
| RAM        | 2 GB                 | 4 GB        |
| Almacenamiento | 10 GB disponibles | 20 GB SSD   |
| Red | Ethernet 100 Mbps | Gigabit Ethernet |

### Software

| Componente | Versión | Descripción |
|------------|---------|-------------|
| Sistema Operativo | Ubuntu 20.04+ / Debian 11+ | Linux recomendado |
| Python | 3.10 - 3.12 | Lenguaje de programación |
| SQLite | 3.31+ | Base de datos embebida |
| Git | 2.x | Control de versiones |

### Dependencias Python

Las dependencias están definidas en `requirements.txt`:

```txt
# Protocolo DLMS/COSEM
dlms-cosem==22.3.0

# Comunicación MQTT
tb-mqtt-client>=1.13.0
tb-paho-mqtt-client>=2.1.2
paho-mqtt>=2.0.0

# Base de datos ORM
sqlalchemy>=2.0.0

# Monitoreo del sistema
psutil>=5.9.0

# Utilidades
python-dateutil>=2.8.0
requests>=2.31.0
```

**Dependencias opcionales** (solo para módulo admin):
```txt
fastapi==0.104.1       # API REST
streamlit==1.28.2      # Dashboard web
uvicorn>=0.24.0        # Servidor ASGI
```

### Medidores Compatibles

El sistema es compatible con medidores que cumplan:
- ✅ Protocolo **DLMS/COSEM** (IEC 62056)
- ✅ Interfaz **Ethernet TCP/IP** (puerto 3333 estándar)
- ✅ Soporte para **HDLC** (High-Level Data Link Control)
- ✅ Implementación de **códigos OBIS** estándar

**Medidores probados:**
- Microstar DLMS
- [Añadir otros modelos probados]

---

## 🚀 Instalación y Configuración

### Paso 1: Clonar el Repositorio

```bash
# Clonar desde repositorio Git
git clone https://github.com/[tu-usuario]/[nombre-repo].git
cd [nombre-repo]/dlms_telemetry_orchestrator

# O descargar y extraer ZIP
wget https://github.com/[tu-usuario]/[nombre-repo]/archive/main.zip
unzip main.zip
cd [nombre-repo]-main/dlms_telemetry_orchestrator
```

### Paso 2: Crear Entorno Virtual

```bash
# Crear entorno virtual Python
python3 -m venv venv

# Activar entorno virtual
source venv/bin/activate  # En Linux/macOS
# venv\Scripts\activate   # En Windows

# Verificar activación (debe mostrar (venv) en el prompt)
which python3
```

### Paso 3: Instalar Dependencias

```bash
# Actualizar pip
pip install --upgrade pip

# Instalar dependencias principales
pip install -r requirements.txt

# (Opcional) Instalar dependencias de administración
pip install -r requirements-admin.txt

# Verificar instalación
pip list | grep -E "dlms-cosem|paho-mqtt|sqlalchemy"
```

### Paso 4: Configurar Base de Datos

La base de datos SQLite se crea automáticamente en la primera ejecución. Para configurar manualmente:

```bash
# Verificar que existe la estructura
ls -lh data/admin.db

# Explorar estructura (opcional)
sqlite3 data/admin.db ".schema meters"
```

### Paso 5: Configurar Medidores

Hay dos formas de añadir medidores:

#### Opción A: Mediante Script Python

```python
# crear_medidor.py
import sqlite3
from datetime import datetime

conn = sqlite3.connect('data/admin.db')
cursor = conn.cursor()

# Insertar medidor
cursor.execute("""
    INSERT INTO meters (
        name, ip_address, port, 
        client_id, server_id, password,
        status, tb_enabled, tb_host, tb_port, tb_token
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
""", (
    'Medidor_Principal',      # Nombre descriptivo
    '192.168.1.128',          # IP del medidor
    3333,                     # Puerto TCP (estándar DLMS)
    1,                        # Client SAP ID
    1,                        # Server Physical ID
    '00000000',               # Password (8 dígitos)
    'active',                 # Estado: active/inactive
    1,                        # ThingsBoard habilitado
    'localhost',              # Host ThingsBoard
    1883,                     # Puerto MQTT ThingsBoard
    'TU_TOKEN_THINGSBOARD'    # Token del dispositivo
))

conn.commit()
conn.close()
print("✅ Medidor configurado exitosamente")
```

Ejecutar:
```bash
python3 crear_medidor.py
```

#### Opción B: Mediante SQL Directo

```bash
sqlite3 data/admin.db << EOF
INSERT INTO meters (
    name, ip_address, port, client_id, server_id, password,
    status, tb_enabled, tb_host, tb_port, tb_token
) VALUES (
    'Medidor_Principal',
    '192.168.1.128',
    3333,
    1,
    1,
    '00000000',
    'active',
    1,
    'localhost',
    1883,
    'TU_TOKEN_THINGSBOARD'
);
EOF
```

### Paso 6: Verificar Configuración

```bash
# Ver medidores configurados
python3 meter_cli.py list

# Salida esperada:
# ID  Name                 IP:Port              Status
# 1   Medidor_Principal    192.168.1.128:3333   active

# Probar conectividad TCP
python3 meter_cli.py test 1

# Salida esperada:
# ✅ TCP connection successful to 192.168.1.128:3333
```

### Paso 7: Configurar ThingsBoard (Externo)

Este sistema requiere una instancia de ThingsBoard funcionando. Puedes usar:

#### Opción A: ThingsBoard Demo Cloud
```
URL: https://demo.thingsboard.io
- Crear cuenta gratuita
- Crear dispositivo en Devices
- Copiar Access Token
- Usar en configuración del medidor
```

#### Opción B: Instalación Local
```bash
# Docker (recomendado)
docker run -d --name thingsboard \
  -p 1883:1883 -p 8080:8080 \
  -v ~/.mytb-data:/data \
  thingsboard/tb-postgres

# Acceder a: http://localhost:8080
# Usuario: tenant@thingsboard.org
# Password: tenant
```

**Pasos en ThingsBoard:**
1. Ir a **Devices** → **Add Device**
2. Nombre: `Medidor_Principal`
3. Device Profile: `Default`
4. Copiar **Access Token** generado
5. Pegar token en la configuración del medidor (campo `tb_token`)

---

## ▶️ Ejecución del Sistema

### Modo Desarrollo (Interactivo)

Para pruebas y desarrollo:

```bash
# Activar entorno virtual
source venv/bin/activate

# Ejecutar script principal
python3 dlms_multi_meter_bridge.py

# Salida esperada:
# 2025-11-19 10:30:45 - [MultiMeterBridge] - INFO - ✓ Network monitor initialized
# 2025-11-19 10:30:45 - [MultiMeterBridge] - INFO - Starting DLMS Multi-Meter Bridge
# 2025-11-19 10:30:45 - [MultiMeterBridge] - INFO - Found 1 active meters
# 2025-11-19 10:30:45 - [Meter[1:Medidor_Principal]] - INFO - Starting worker
# 2025-11-19 10:30:46 - [Meter[1:Medidor_Principal]] - INFO - ✓ DLMS connection established
# 2025-11-19 10:30:46 - [Meter[1:Medidor_Principal]] - INFO - ✓ MQTT Connected
# 2025-11-19 10:30:47 - [Meter[1:Medidor_Principal]] - INFO - ✓ Cycle 1 successful
```

**Detener con:** `Ctrl + C`

### Modo Producción (Servicio systemd)

Para ejecución continua en servidor:

#### 1. Crear archivo de servicio

```bash
sudo nano /etc/systemd/system/dlms-telemetry.service
```

Contenido:
```ini
[Unit]
Description=DLMS Multi-Meter Telemetry Service
Documentation=https://github.com/[tu-usuario]/[tu-repo]
After=network.target

[Service]
Type=simple
User=pi
Group=pi
WorkingDirectory=/home/pi/dlms_telemetry_orchestrator
Environment="PATH=/home/pi/dlms_telemetry_orchestrator/venv/bin"
ExecStart=/home/pi/dlms_telemetry_orchestrator/venv/bin/python3 dlms_multi_meter_bridge.py

# Reinicio automático
Restart=always
RestartSec=10

# Límites de recursos
MemoryLimit=512M
CPUQuota=50%

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=dlms-telemetry

# Seguridad
NoNewPrivileges=true
PrivateTmp=true

[Install]
WantedBy=multi-user.target
```

#### 2. Activar y gestionar servicio

```bash
# Recargar systemd
sudo systemctl daemon-reload

# Habilitar inicio automático
sudo systemctl enable dlms-telemetry.service

# Iniciar servicio
sudo systemctl start dlms-telemetry.service

# Verificar estado
sudo systemctl status dlms-telemetry.service

# Ver logs en tiempo real
sudo journalctl -u dlms-telemetry.service -f

# Ver últimas 100 líneas
sudo journalctl -u dlms-telemetry.service -n 100

# Reiniciar servicio
sudo systemctl restart dlms-telemetry.service

# Detener servicio
sudo systemctl stop dlms-telemetry.service
```

### Verificación de Funcionamiento

```bash
# 1. Verificar proceso corriendo
ps aux | grep dlms_multi_meter_bridge

# 2. Ver logs recientes
tail -f logs/multi_meter_bridge.log

# 3. Verificar estado de medidores
python3 meter_cli.py status 1

# 4. Verificar publicación MQTT (requiere mosquitto-clients)
mosquitto_sub -h localhost -p 1883 -t "v1/devices/+/telemetry" -u "TU_TOKEN" -v
```

---

## 📊 Códigos OBIS Soportados

El sistema lee las siguientes variables eléctricas usando códigos OBIS estándar:

| Código OBIS | Variable | Unidad | Descripción |
|-------------|----------|--------|-------------|
| 1-1:32.7.0 | voltage_l1 | V | Voltaje instantáneo Fase A |
| 1-1:31.7.0 | current_l1 | A | Corriente instantánea Fase A |
| 1-1:14.7.0 | frequency | Hz | Frecuencia de la red eléctrica |
| 1-1:1.7.0 | active_power | W | Potencia activa total |
| 1-1:1.8.0 | active_energy | Wh | Energía activa acumulada (importada) |
| 1-1:52.7.0 | voltage_l2 | V | Voltaje instantáneo Fase B |
| 1-1:51.7.0 | current_l2 | A | Corriente instantánea Fase B |
| 1-1:72.7.0 | voltage_l3 | V | Voltaje instantáneo Fase C |
| 1-1:71.7.0 | current_l3 | A | Corriente instantánea Fase C |

**Nota:** Los códigos leídos son configurables en el módulo `dlms_poller_production.py`.

---

## 🔧 Parámetros de Configuración

### Configuración en Base de Datos

Los siguientes parámetros se configuran por medidor en la tabla `meters`:

| Parámetro | Tipo | Descripción | Ejemplo |
|-----------|------|-------------|---------|
| `name` | VARCHAR(100) | Nombre descriptivo del medidor | "Medidor_Principal" |
| `ip_address` | VARCHAR(45) | Dirección IP del medidor | "192.168.1.128" |
| `port` | INTEGER | Puerto TCP del medidor | 3333 |
| `client_id` | INTEGER | DLMS Client SAP ID | 1 |
| `server_id` | INTEGER | DLMS Server Physical ID | 1 |
| `password` | VARCHAR(50) | Password DLMS (8 dígitos) | "00000000" |
| `status` | VARCHAR(20) | Estado del medidor | "active" / "inactive" |
| `tb_enabled` | BOOLEAN | Habilitar publicación ThingsBoard | 1 (true) |
| `tb_host` | VARCHAR(255) | Host de ThingsBoard | "localhost" |
| `tb_port` | INTEGER | Puerto MQTT de ThingsBoard | 1883 |
| `tb_token` | VARCHAR(100) | Token del dispositivo | "ABC123..." |

### Parámetros del Sistema

Configurables en `dlms_multi_meter_bridge.py`:

```python
# Intervalo de polling (segundos)
POLLING_INTERVAL = 2.0  # Lectura cada 2 segundos

# Timeouts de conexión
DLMS_TIMEOUT = 7.0      # Timeout para lectura DLMS
MQTT_KEEPALIVE = 60     # Keepalive MQTT en segundos

# Auto-recuperación
MAX_RETRIES = 3                    # Reintentos por lectura
RETRY_DELAY = 3.0                  # Delay entre reintentos
MAX_CONSECUTIVE_ERRORS = 15        # Errores antes de reconectar
CIRCUIT_BREAKER_THRESHOLD = 10     # Reconexiones/hora antes de pausar
CIRCUIT_BREAKER_PAUSE = 300        # Pausa del circuit breaker (segundos)

# Watchdog
MAX_SILENCE_MINUTES = 10  # Reconectar si no hay lecturas exitosas
```

---

## 🛡️ Sistema de Auto-Recuperación

El sistema implementa 3 niveles de recuperación ante fallos:

### Nivel 1: Retry Automático
```
Fallo en lectura DLMS
    ↓
Reintento inmediato (hasta 3 veces)
    ↓
Delay de 3 segundos entre reintentos
    ↓
¿Éxito? → SÍ → Continuar
         NO → Nivel 2
```

**Configuración:**
```python
MAX_RETRIES = 3
RETRY_DELAY = 3.0
```

### Nivel 2: Reconexión DLMS
```
15 errores consecutivos
    ↓
Cerrar conexión TCP/DLMS
    ↓
Esperar 5 segundos
    ↓
Nueva conexión + Re-autenticación
    ↓
¿Éxito? → SÍ → Reset contador
         NO → Nivel 3
```

**Configuración:**
```python
MAX_CONSECUTIVE_ERRORS = 15
```

### Nivel 3: Circuit Breaker
```
10 reconexiones en 1 hora
    ↓
🚨 ACTIVAR CIRCUIT BREAKER
    ↓
Pausar intentos 5 minutos
    ↓
Crear alarma en BD
    ↓
Log ERROR crítico
    ↓
Después de 5 min → Reintentar desde Nivel 1
```

**Configuración:**
```python
CIRCUIT_BREAKER_THRESHOLD = 10  # reconexiones/hora
CIRCUIT_BREAKER_PAUSE = 300     # segundos
```

---

## 📈 Monitoreo y Métricas

### Ver Estado en Tiempo Real

```bash
# Listar medidores
python3 meter_cli.py list

# Ver estado detallado de medidor específico
python3 meter_cli.py status 1

# Salida:
# ┌────────────────────────────────────────────┐
# │  Medidor: Medidor_Principal (ID: 1)       │
# │  IP: 192.168.1.128:3333                    │
# │  Estado: 🟢 ACTIVO                          │
# ├────────────────────────────────────────────┤
# │  Tasa de Éxito DLMS:  ████████░░ 95.2%    │
# │  Tasa Publicación MQTT: █████████░ 99.8%  │
# │                                            │
# │  Ciclos: 1523/1600 (77 fallos)            │
# │  Uptime: 0h 53m 20s                        │
# │  Última lectura: hace 2 segundos           │
# │                                            │
# │  Valores actuales:                         │
# │    Voltaje: 220.5V                         │
# │    Corriente: 5.2A                         │
# │    Frecuencia: 60.01Hz                     │
# │    Potencia: 1146.6W                       │
# │    Energía: 12543.2Wh                      │
# └────────────────────────────────────────────┘
```

### Consultar Métricas Históricas

```python
# consultar_metricas.py
import sqlite3
from datetime import datetime, timedelta

conn = sqlite3.connect('data/admin.db')
cursor = conn.cursor()

# Obtener últimas 10 mediciones
cursor.execute("""
    SELECT timestamp, measurement_name, value, unit
    FROM metrics
    WHERE meter_id = 1
    ORDER BY timestamp DESC
    LIMIT 10
""")

print("Últimas 10 mediciones:")
for row in cursor.fetchall():
    print(f"{row[0]} - {row[1]}: {row[2]} {row[3]}")

# Obtener promedio de voltaje última hora
una_hora_atras = datetime.now() - timedelta(hours=1)
cursor.execute("""
    SELECT AVG(value) as promedio
    FROM metrics
    WHERE meter_id = 1
      AND measurement_name = 'voltage_l1'
      AND timestamp > ?
""", (una_hora_atras,))

promedio = cursor.fetchone()[0]
print(f"\nPromedio voltaje última hora: {promedio:.2f}V")

conn.close()
```

### Ver Alarmas

```python
# consultar_alarmas.py
import sqlite3

conn = sqlite3.connect('data/admin.db')
cursor = conn.cursor()

cursor.execute("""
    SELECT timestamp, severity, message, resolved
    FROM alarms
    WHERE meter_id = 1
    ORDER BY timestamp DESC
    LIMIT 20
""")

print("Últimas 20 alarmas:")
for row in cursor.fetchall():
    estado = "✓ Resuelta" if row[3] else "⚠ Activa"
    print(f"{row[0]} [{row[1]}] {row[2]} - {estado}")

conn.close()
```

---

## 🔍 Solución de Problemas

### Problema 1: Error de Instalación de Dependencias

**Síntoma:**
```
ERROR: Could not find a version that satisfies the requirement dlms-cosem
```

**Solución:**
```bash
# Actualizar pip
pip install --upgrade pip setuptools wheel

# Reinstalar
pip install -r requirements.txt

# Si persiste, instalar manualmente
pip install dlms-cosem==22.3.0
```

### Problema 2: No se Puede Conectar al Medidor

**Síntoma:**
```
ERROR - Failed to connect to 192.168.1.128:3333 - Connection refused
```

**Diagnóstico:**
```bash
# 1. Verificar conectividad de red
ping 192.168.1.128

# 2. Verificar puerto TCP abierto
nc -zv 192.168.1.128 3333
# o
telnet 192.168.1.128 3333

# 3. Verificar firewall
sudo iptables -L | grep 3333

# 4. Verificar configuración del medidor
python3 meter_cli.py test 1
```

**Soluciones:**
- Verificar que el medidor esté encendido y en la red
- Verificar que la IP sea correcta
- Verificar que el puerto 3333 esté abierto en el firewall
- Verificar cables Ethernet

### Problema 3: Autenticación DLMS Fallida

**Síntoma:**
```
ERROR - DLMS authentication failed: Association rejected (code 0x01)
```

**Diagnóstico:**
```python
# Verificar credenciales en BD
import sqlite3
conn = sqlite3.connect('data/admin.db')
cursor = conn.cursor()
cursor.execute("SELECT client_id, server_id, password FROM meters WHERE id=1")
print(cursor.fetchone())
conn.close()
```

**Soluciones:**
- Verificar que `client_id` sea correcto (típicamente 1)
- Verificar que `server_id` sea correcto (típicamente 1)
- Verificar que `password` sea correcto (8 dígitos, típicamente "00000000")
- Consultar manual del medidor para credenciales correctas

### Problema 4: Publicación MQTT Falla

**Síntoma:**
```
ERROR - MQTT connection failed: code 5 - Not authorized
```

**Diagnóstico:**
```bash
# Verificar token en BD
sqlite3 data/admin.db "SELECT tb_token FROM meters WHERE id=1;"

# Probar conexión MQTT manual
mosquitto_pub -h localhost -p 1883 -u "TU_TOKEN" -t "v1/devices/me/telemetry" -m '{"test":1}'
```

**Soluciones:**
- Verificar que el token de ThingsBoard sea correcto
- Verificar que ThingsBoard esté corriendo en el host/puerto configurado
- Verificar conectividad de red a ThingsBoard
- Regenerar token en ThingsBoard si es necesario

### Problema 5: Alto Uso de CPU/RAM

**Síntoma:**
Sistema consume >50% CPU o >500MB RAM

**Diagnóstico:**
```bash
# Ver uso de recursos
top -p $(pgrep -f dlms_multi_meter_bridge)

# Ver conexiones de red
netstat -tupn | grep python3
```

**Soluciones:**
- Aumentar `POLLING_INTERVAL` a 5-10 segundos
- Reducir nivel de logging de DEBUG a INFO
- Verificar que no haya múltiples instancias corriendo
- Aumentar `DLMS_TIMEOUT` para reducir reintentos

### Problema 6: Base de Datos Corrupta

**Síntoma:**
```
sqlite3.DatabaseError: database disk image is malformed
```

**Solución:**
```bash
# Backup de BD actual
cp data/admin.db data/admin.db.backup

# Intentar reparación
sqlite3 data/admin.db ".dump" | sqlite3 data/admin_recovered.db

# Si falla, restaurar desde backup o crear nueva BD
rm data/admin.db
python3 dlms_multi_meter_bridge.py  # Crea nueva BD automáticamente
```

---

## 📚 Estructura del Proyecto

```
dlms_telemetry_orchestrator/
├── README.md                      # Este archivo
├── requirements.txt               # Dependencias Python
├── requirements-admin.txt         # Dependencias opcionales admin
│
├── dlms_multi_meter_bridge.py    # ⭐ SCRIPT PRINCIPAL
├── dlms_poller_production.py     # Cliente DLMS optimizado
├── dlms_reader.py                # Cliente DLMS base
├── tb_mqtt_client.py             # Cliente MQTT ThingsBoard
├── network_monitor.py            # Monitor de conectividad red
├── mqtt_publisher.py             # Publicador MQTT genérico
├── meter_cli.py                  # CLI de gestión
├── meter_control_api.py          # API REST de control
│
├── admin/                        # Módulo de administración
│   ├── __init__.py
│   ├── database.py              # ORM y acceso a datos
│   ├── api.py                   # API REST FastAPI
│   ├── dashboard.py             # Dashboard Streamlit
│   ├── alarm_monitor.py         # Monitor de alarmas
│   └── orchestrator.py          # Orquestador avanzado
│
├── config/                       # Configuraciones
│   └── logrotate.conf           # Rotación de logs
│
├── data/                         # Datos persistentes
│   └── admin.db                 # Base de datos SQLite
│
├── logs/                         # Archivos de log
│   ├── multi_meter_bridge.log   # Log principal
│   ├── api.log                  # Log de API
│   └── dashboard.log            # Log de dashboard
│
├── docs/                         # Documentación técnica
│   ├── ARQUITECTURA_FINAL.md
│   ├── GUIA_PRODUCCION.md
│   └── [otros documentos]
│
├── gateway/                      # Configs ThingsBoard Gateway (opcional)
│   ├── config/
│   ├── README.md
│   └── setup_gateway.sh
│
└── venv/                         # Entorno virtual Python (generado)
```

---

## 🧪 Pruebas y Validación

### Prueba 1: Conectividad TCP

```bash
# Probar conexión TCP básica
python3 meter_cli.py test 1

# Salida esperada:
# Testing TCP connection to 192.168.1.128:3333...
# ✅ Connection successful
# Response time: 45ms
```

### Prueba 2: Lectura DLMS

```python
# test_dlms_reading.py
from dlms_poller_production import ProductionDLMSPoller

# Crear poller
poller = ProductionDLMSPoller(
    host='192.168.1.128',
    port=3333,
    password='00000000',
    client_sap=1,
    server_id=1
)

# Conectar
if poller.connect():
    print("✅ DLMS connection successful")
    
    # Leer una medición
    readings = poller.poll_once()
    
    if readings:
        print("✅ Readings obtained:")
        for key, value in readings.items():
            print(f"  {key}: {value}")
    else:
        print("❌ Failed to read measurements")
        
    poller.disconnect()
else:
    print("❌ Failed to connect")
```

Ejecutar:
```bash
python3 test_dlms_reading.py
```

### Prueba 3: Publicación MQTT

```python
# test_mqtt_publish.py
from tb_mqtt_client import ThingsBoardMQTTClient
import time

# Crear cliente
client = ThingsBoardMQTTClient(
    host='localhost',
    port=1883,
    token='TU_TOKEN_THINGSBOARD'
)

# Conectar
if client.connect():
    print("✅ MQTT connected")
    
    # Enviar telemetría de prueba
    test_data = {
        "voltage": 220.5,
        "current": 5.2,
        "frequency": 60.0,
        "power": 1146.6,
        "energy": 12543.2
    }
    
    if client.send_telemetry(test_data):
        print("✅ Telemetry sent successfully")
    else:
        print("❌ Failed to send telemetry")
    
    time.sleep(2)
    client.disconnect()
else:
    print("❌ Failed to connect to MQTT broker")
```

Ejecutar:
```bash
python3 test_mqtt_publish.py
```

### Prueba 4: Sistema Completo

```bash
# Ejecutar en modo desarrollo con logging DEBUG
python3 dlms_multi_meter_bridge.py

# Dejar corriendo 5 minutos

# En otra terminal, verificar métricas
python3 meter_cli.py status 1

# Verificar que:
# - Success rate > 90%
# - MQTT publish rate > 95%
# - No hay alarmas críticas
# - Uptime incrementa correctamente
```

---

## 📊 Formato de Datos

### Formato de Telemetría MQTT (JSON)

El sistema envía datos a ThingsBoard en el siguiente formato:

```json
{
  "voltage_l1": 220.5,
  "current_l1": 5.2,
  "frequency": 60.01,
  "active_power": 1146.6,
  "active_energy": 12543.2,
  "voltage_l2": 220.3,
  "current_l2": 5.1,
  "voltage_l3": 220.7,
  "current_l3": 5.3
}
```

**Topic MQTT:** `v1/devices/me/telemetry`  
**QoS:** 1 (at-least-once delivery)  
**Frecuencia:** Cada 2 segundos (configurable)

### Esquema de Base de Datos

#### Tabla: meters
```sql
CREATE TABLE meters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    ip_address VARCHAR(45) NOT NULL,
    port INTEGER DEFAULT 3333,
    client_id INTEGER DEFAULT 1,
    server_id INTEGER DEFAULT 1,
    password VARCHAR(50) DEFAULT '00000000',
    status VARCHAR(20) DEFAULT 'active',
    tb_enabled BOOLEAN DEFAULT 1,
    tb_host VARCHAR(255) DEFAULT 'localhost',
    tb_port INTEGER DEFAULT 1883,
    tb_token VARCHAR(100),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

#### Tabla: metrics
```sql
CREATE TABLE metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    meter_id INTEGER NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    measurement_name VARCHAR(50) NOT NULL,
    value REAL NOT NULL,
    unit VARCHAR(20),
    FOREIGN KEY (meter_id) REFERENCES meters(id)
);
```

#### Tabla: alarms
```sql
CREATE TABLE alarms (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    meter_id INTEGER NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    severity VARCHAR(20) NOT NULL,  -- INFO, WARNING, ERROR, CRITICAL
    message TEXT NOT NULL,
    resolved BOOLEAN DEFAULT 0,
    resolved_at DATETIME,
    FOREIGN KEY (meter_id) REFERENCES meters(id)
);
```

---

## 🔒 Consideraciones de Seguridad

### Credenciales

- ✅ Almacenar passwords DLMS en base de datos (no en código)
- ✅ Usar tokens únicos por dispositivo en ThingsBoard
- ⚠️ NO compartir tokens en repositorios públicos
- ⚠️ Cambiar passwords por defecto en medidores

### Red

- ✅ Usar VLAN segregada para medidores
- ✅ Configurar firewall para permitir solo puerto 3333
- ✅ Usar MQTT con TLS/SSL en producción
- ⚠️ NO exponer medidores directamente a Internet

### Sistema

- ✅ Ejecutar servicio con usuario no-root
- ✅ Habilitar `NoNewPrivileges` en systemd
- ✅ Limitar recursos con `MemoryLimit` y `CPUQuota`
- ✅ Mantener sistema operativo actualizado

---

## 📖 Referencias

### Estándares y Protocolos

- **DLMS/COSEM:** [IEC 62056](https://www.dlms.com/)
- **MQTT:** [MQTT Version 3.1.1](https://docs.oasis-open.org/mqtt/mqtt/v3.1.1/mqtt-v3.1.1.html)
- **ThingsBoard API:** [ThingsBoard Documentation](https://thingsboard.io/docs/)

### Bibliotecas Utilizadas

- **dlms-cosem:** [GitHub](https://github.com/pwitab/dlms-cosem)
- **paho-mqtt:** [Eclipse Paho](https://www.eclipse.org/paho/index.php?page=clients/python/index.php)
- **SQLAlchemy:** [Documentation](https://www.sqlalchemy.org/)

### Artículos y Tutoriales

- [Understanding DLMS/COSEM Protocol](https://www.dlms.com/documentation/)
- [ThingsBoard IoT Gateway](https://thingsboard.io/docs/iot-gateway/)
- [MQTT QoS Explained](https://www.hivemq.com/blog/mqtt-essentials-part-6-mqtt-quality-of-service-levels/)

---

## 👥 Contribuciones y Soporte

### Autor

**Brayan Ricardo Pisso Ramírez**  
Estudiante de Ingeniería Electrónica  
Universidad Nacional de Colombia - Sede Manizales  
Email: [tu-email@unal.edu.co]

### Director de Tesis

**[Nombre del Director]**  
[Título y Cargo]  
Universidad Nacional de Colombia - Sede Manizales  
Email: [email-director@unal.edu.co]

### Repositorio

GitHub: [https://github.com/[tu-usuario]/[nombre-repo]]

### Reporte de Issues

Para reportar problemas o sugerir mejoras:
1. Ir a la pestaña **Issues** en GitHub
2. Crear nuevo issue con etiqueta apropiada (`bug`, `enhancement`, `question`)
3. Incluir:
   - Descripción detallada del problema
   - Pasos para reproducir
   - Logs relevantes
   - Versión del sistema

---

## 📜 Licencia

[Especificar licencia - MIT, GPL, Apache, etc.]

```
Copyright (c) 2025 Brayan Ricardo Pisso Ramírez

[Texto de la licencia]
```

---

## 🙏 Agradecimientos

- Universidad Nacional de Colombia - Sede Manizales
- [Nombre del Director] - Por la dirección y asesoría del proyecto
- [Otros colaboradores/instituciones si aplica]
- Comunidad open-source de dlms-cosem, paho-mqtt y ThingsBoard

---

## 📅 Historial de Versiones

### v2.2.0 (2025-11-19) - Versión Actual
- ✅ Sistema completo multi-medidor funcional
- ✅ Auto-recuperación de 3 niveles implementada
- ✅ Circuit breaker para prevención de loops
- ✅ CLI de gestión completa
- ✅ Optimización de velocidad con caché de scalers
- ✅ Documentación completa

### v2.1.0 (2025-11-10)
- Implementación de arquitectura Gateway opcional
- Resolución de conflictos MQTT (code 7)
- Sistema de alarmas

### v2.0.0 (2025-10-30)
- Migración a arquitectura multi-medidor
- Base de datos SQLite
- Workers asíncronos con asyncio

### v1.0.0 (2025-10-01)
- Primera versión funcional
- Soporte para medidor único
- Publicación MQTT básica

---

**Última actualización:** 19 de Noviembre 2025  
**Estado del proyecto:** ✅ Producción - Estable  
**Versión de documentación:** 2.2.0
````