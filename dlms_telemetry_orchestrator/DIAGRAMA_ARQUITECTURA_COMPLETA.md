# 🏗️ ARQUITECTURA COMPLETA DEL SISTEMA DLMS
## De Medidores a ThingsBoard - Todas las Capas

```
================================================================================
                    ARQUITECTURA EN 7 CAPAS
================================================================================

┌─────────────────────────────────────────────────────────────────────────────┐
│ CAPA 1: MEDIDORES FÍSICOS (Hardware DLMS)                                   │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┴────────────────┐
                    │                                │
            ┌───────▼────────┐              ┌───────▼────────┐
            │  MEDIDOR 1     │              │  MEDIDOR 2     │
            │                │              │                │
            │ IP: 192.168.1.128            │ IP: 192.168.1.135
            │ Puerto: 3333   │              │ Puerto: 3333   │
            │                │              │                │
            │ Protocolo:     │              │ Protocolo:     │
            │ • TCP/IP       │              │ • TCP/IP       │
            │ • HDLC         │              │ • HDLC         │
            │ • DLMS/COSEM   │              │ • DLMS/COSEM   │
            │                │              │                │
            │ Credenciales:  │              │ Credenciales:  │
            │ • client_sap=1 │              │ • client_sap=1 │
            │ • server_id=1  │              │ • server_id=1  │
            │ • pass=00000000│              │ • pass=00000000│
            └────────────────┘              └────────────────┘
                    │                                │
                    │  TCP Socket                    │  TCP Socket
                    │  (Raw DLMS)                    │  (Raw DLMS)
                    │                                │
┌─────────────────────────────────────────────────────────────────────────────┐
│ CAPA 2: CLIENTE DLMS (Python - Lectura de Medidores)                        │
└─────────────────────────────────────────────────────────────────────────────┘
                    │                                │
                    └────────────┬───────────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │  dlms_reader.py         │
                    │  (DLMSClient)           │
                    │                         │
                    │  Funciones:             │
                    │  • connect()            │
                    │  • read_measurements()  │
                    │  • disconnect()         │
                    │                         │
                    │  Manejo de:             │
                    │  • HDLC framing         │
                    │  • AARQ/AARE handshake  │
                    │  • COSEM get-request    │
                    │  • Error handling       │
                    └─────────────────────────┘
                                 │
                                 │  Readings (dict)
                                 │
┌─────────────────────────────────────────────────────────────────────────────┐
│ CAPA 3: POLLER DE PRODUCCIÓN (Auto-recuperación + QoS)                      │
└─────────────────────────────────────────────────────────────────────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │ dlms_poller_production.py│
                    │ (DLMSProductionPoller)   │
                    │                          │
                    │ Componentes QoS:         │
                    │ ┌──────────────────────┐ │
                    │ │ Auto-Recuperación    │ │
                    │ │ • Retry automático   │ │
                    │ │ • Backoff exponencial│ │
                    │ │ • Never give up      │ │
                    │ └──────────────────────┘ │
                    │ ┌──────────────────────┐ │
                    │ │ Circuit Breaker      │ │
                    │ │ • Max 10 reconnect/h │ │
                    │ │ • Pausa 5 minutos    │ │
                    │ └──────────────────────┘ │
                    │ ┌──────────────────────┐ │
                    │ │ Watchdog Silencio    │ │
                    │ │ • 10 min sin lecturas│ │
                    │ │ • Reconexión forzada │ │
                    │ └──────────────────────┘ │
                    │ ┌──────────────────────┐ │
                    │ │ Watchdog HDLC        │ │
                    │ │ • 15 errores consec. │ │
                    │ │ • Limpieza de buffer │ │
                    │ └──────────────────────┘ │
                    │ ┌──────────────────────┐ │
                    │ │ Buffer Cleaner       │ │
                    │ │ • Limpieza TCP buffer│ │
                    │ │ • Sync recovery      │ │
                    │ └──────────────────────┘ │
                    └──────────────────────────┘
                                 │
                                 │  Readings + Metadata
                                 │
┌─────────────────────────────────────────────────────────────────────────────┐
│ CAPA 4: ORQUESTADOR MULTI-MEDIDOR (Gestión Concurrente)                     │
└─────────────────────────────────────────────────────────────────────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │ dlms_multi_meter_bridge.py│
                    │ (MultiMeterBridge)       │
                    │                          │
                    │ Funciones:               │
                    │ ┌──────────────────────┐ │
                    │ │ load_meters_from_db()│ │
                    │ │ • Lee config de DB   │ │
                    │ │ • Carga credenciales │ │
                    │ └──────────────────────┘ │
                    │ ┌──────────────────────┐ │
                    │ │ MeterWorker (Thread) │ │
                    │ │ • 1 thread/medidor   │ │
                    │ │ • Individual MQTT    │ │
                    │ │ • Isolation de fallos│ │
                    │ └──────────────────────┘ │
                    │ ┌──────────────────────┐ │
                    │ │ Monitor Loop         │ │
                    │ │ • Reportes cada 60s  │ │
                    │ │ • Métricas en logs   │ │
                    │ └──────────────────────┘ │
                    │ ┌──────────────────────┐ │
                    │ │ Network Monitor      │ │
                    │ │ • Ping monitoring    │ │
                    │ │ • Alarmas de red     │ │
                    │ └──────────────────────┘ │
                    └──────────────────────────┘
                         │              │
                  Worker 1          Worker 2
                 (Medidor 1)      (Medidor 2)
                         │              │
                         │  JSON        │  JSON
                         │  Telemetry   │  Telemetry
                         │              │
┌─────────────────────────────────────────────────────────────────────────────┐
│ CAPA 5: MQTT LOCAL (Mosquitto Broker)                                       │
└─────────────────────────────────────────────────────────────────────────────┘
                         │              │
                         └──────┬───────┘
                                │
                    ┌───────────▼────────────┐
                    │  Mosquitto             │
                    │  (MQTT Broker)         │
                    │                        │
                    │  Puerto: 1884          │
                    │  QoS: 1                │
                    │  Auth: None            │
                    │                        │
                    │  Topics:               │
                    │  • v1/devices/me/      │
                    │    telemetry           │
                    │  • v1/devices/me/      │
                    │    attributes          │
                    └────────────────────────┘
                                │
                                │  MQTT Messages
                                │  (QoS=1)
                                │
┌─────────────────────────────────────────────────────────────────────────────┐
│ CAPA 6: GATEWAY MQTT (Bridge a ThingsBoard)                                 │
└─────────────────────────────────────────────────────────────────────────────┘
                                │
                    ┌───────────▼────────────┐
                    │ ThingsBoard Gateway    │
                    │ (tb-gateway)           │
                    │                        │
                    │ PID: 110202            │
                    │                        │
                    │ Función:               │
                    │ • Suscribe a port 1884 │
                    │ • Transforma mensajes  │
                    │ • Publica a TB (1883)  │
                    │ • Maneja tokens        │
                    │                        │
                    │ Config:                │
                    │ /var/lib/thingsboard_  │
                    │  gateway/config/       │
                    └────────────────────────┘
                                │
                                │  MQTT + Auth Token
                                │
┌─────────────────────────────────────────────────────────────────────────────┐
│ CAPA 7: THINGSBOARD SERVER (Telemetría y Visualización)                     │
└─────────────────────────────────────────────────────────────────────────────┘
                                │
                    ┌───────────▼────────────┐
                    │  ThingsBoard Server    │
                    │                        │
                    │  PID: 40620            │
                    │                        │
                    │  Puertos:              │
                    │  • 1883: MQTT          │
                    │  • 8080: Web UI        │
                    │  • 9090: RPC           │
                    │                        │
                    │  Componentes:          │
                    │  • Device Manager      │
                    │  • Rule Engine         │
                    │  • Dashboard           │
                    │  • Alertas             │
                    │  • PostgreSQL DB       │
                    └────────────────────────┘
                                │
                                │
                    ┌───────────▼────────────┐
                    │  Dashboard Web UI      │
                    │                        │
                    │  http://localhost:8080 │
                    │                        │
                    │  Visualización:        │
                    │  • Gráficas en tiempo  │
                    │    real                │
                    │  • Alarmas             │
                    │  • Históricos          │
                    │  • Telemetría          │
                    └────────────────────────┘

================================================================================
                        FLUJO DE DATOS COMPLETO
================================================================================

1. LECTURA (Cada 1 segundo por medidor):
   Medidor → DLMSClient → ProductionPoller → Worker Thread
   
2. PUBLICACIÓN:
   Worker → Mosquitto (1884) → Gateway → ThingsBoard (1883)
   
3. ALMACENAMIENTO:
   ThingsBoard → PostgreSQL → Dashboard

4. MONITOREO:
   • Logs: journalctl -u dlms-multi-meter.service -f
   • CLI: python3 meter_cli.py status <id>
   • API: http://localhost:5001/api/meters
   • DB: SQLite (data/admin.db) - métricas y alarmas

================================================================================
                        SCRIPTS Y SU FUNCIÓN
================================================================================

SCRIPTS PRINCIPALES:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. dlms_reader.py (380 líneas)
   ├─ Clase: DLMSClient
   ├─ Función: Cliente DLMS bajo nivel
   ├─ Maneja: TCP socket, HDLC framing, COSEM protocol
   └─ Métodos:
      ├─ connect() - Establece conexión TCP + AARQ
      ├─ read_measurement() - Lee un OBIS code
      ├─ read_measurements() - Lee múltiples mediciones
      └─ disconnect() - Cierra conexión limpiamente

2. dlms_poller_production.py (850+ líneas)
   ├─ Clase: DLMSProductionPoller
   ├─ Función: Wrapper robusto con QoS
   ├─ Características:
   │  ├─ Auto-recuperación (infinite retry)
   │  ├─ Circuit Breaker (10 reconnect/hour)
   │  ├─ Watchdog de silencio (10 min)
   │  ├─ Watchdog HDLC (15 errores)
   │  └─ Buffer Cleaner (TCP flush)
   └─ Métodos:
      ├─ poll_once() - Un ciclo de lectura
      ├─ _handle_disconnect() - Auto-recovery logic
      └─ _check_watchdogs() - Monitoreo proactivo

3. dlms_multi_meter_bridge.py (600+ líneas)
   ├─ Clase: MultiMeterBridge
   ├─ Función: Orquestador multi-medidor
   ├─ Arquitectura:
   │  ├─ 1 Thread por medidor (MeterWorker)
   │  ├─ 1 MQTT client por medidor (aislamiento)
   │  └─ Monitor loop (reportes cada 60s)
   └─ Métodos:
      ├─ load_meters_from_db() - Carga config
      ├─ _start_meter_worker() - Inicia worker
      ├─ _create_poller() - Crea poller con QoS
      └─ _monitor_loop() - Reportes de sistema

4. tb_mqtt_client.py (300 líneas)
   ├─ Clase: ThingsBoardMQTT
   ├─ Función: Cliente MQTT para ThingsBoard
   ├─ Características:
   │  ├─ QoS=1 (at-least-once delivery)
   │  ├─ Offline buffering (1000 msgs)
   │  ├─ Auto-reconnect
   │  └─ Retry exponencial
   └─ Métodos:
      ├─ publish_telemetry() - Publica mediciones
      ├─ publish_attributes() - Publica atributos
      └─ _on_disconnect() - Auto-recovery MQTT

SCRIPTS DE MONITOREO Y CONTROL:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

5. meter_cli.py (600+ líneas)
   ├─ CLI completa para control de medidores
   └─ Comandos:
      ├─ list - Lista todos los medidores
      ├─ status <id> - Estado detallado
      ├─ test <id> - Test de conectividad
      ├─ logs <id> - Ver logs filtrados
      ├─ follow <id> - Logs en tiempo real
      ├─ pause <id> - Pausar medidor
      ├─ resume <id> - Reanudar medidor
      ├─ restart <id> - Restart worker
      └─ health - Salud del sistema

6. meter_control_api.py (800+ líneas)
   ├─ API REST Flask (puerto 5001)
   └─ Endpoints:
      ├─ GET /api/meters - Listar todos
      ├─ GET /api/meters/<id>/status - Estado
      ├─ GET /api/meters/<id>/logs - Logs
      ├─ POST /api/meters/<id>/pause - Pausar
      ├─ POST /api/meters/<id>/resume - Reanudar
      ├─ POST /api/meters/<id>/test - Test
      ├─ POST /api/meters/<id>/restart - Restart
      └─ GET /api/system/health - Salud general

7. system_health_monitor.py (500+ líneas)
   ├─ Monitor de salud del sistema
   └─ Reporta:
      ├─ Success rate por medidor
      ├─ MQTT publish rate
      ├─ Latencias promedio
      ├─ Reconexiones
      ├─ Errores HDLC
      └─ Alarmas activas

8. network_monitor.py (400 líneas)
   ├─ Monitor de red integrado
   └─ Funciones:
      ├─ Ping continuo a medidores
      ├─ Detección de caídas de red
      ├─ Alarmas en DB
      └─ Métricas de latencia

SCRIPTS DE BASE DE DATOS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

9. admin/database.py (300 líneas)
   ├─ Modelos SQLAlchemy
   └─ Tablas:
      ├─ meters - Configuración de medidores
      ├─ meter_metrics - Métricas de rendimiento
      ├─ alarms - Alarmas y eventos
      ├─ network_metrics - Métricas de red
      └─ dlms_diagnostics - Diagnósticos DLMS

10. admin/orchestrator.py (500 líneas)
    ├─ Orquestador de alto nivel
    └─ Funciones:
       ├─ Gestión de workers
       ├─ Control de ciclo de vida
       └─ Coordinación de tareas

SCRIPTS DE PROVISIONING:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

11. thingsboard_provisioning.py (400 líneas)
    ├─ Provisiona dispositivos en ThingsBoard
    └─ Funciones:
       ├─ Crea device en TB
       ├─ Obtiene access token
       ├─ Configura dashboard
       └─ Actualiza DB local

12. provision_device.py (200 líneas)
    ├─ Script de provisioning simplificado
    └─ Uso: python3 provision_device.py <meter_id>

SCRIPTS DE SERVICIO:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

13. dlms-mqtt-bridge.service (systemd)
    ├─ Servicio principal
    ├─ ExecStart: python3 dlms_multi_meter_bridge.py
    ├─ Auto-restart: always
    ├─ WorkingDirectory: /path/to/project
    └─ User: root (requiere permisos de red)

14. service-manager.sh (150 líneas)
    ├─ Script de gestión de servicio
    └─ Comandos:
       ├─ start - Inicia servicio
       ├─ stop - Detiene servicio
       ├─ restart - Reinicia servicio
       ├─ status - Estado del servicio
       └─ logs - Ver logs

SCRIPTS DE DIAGNÓSTICO:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

15. qos_health_check.py (350 líneas)
    ├─ Chequeo de salud QoS
    └─ Verifica:
       ├─ Servicios corriendo
       ├─ Conectividad medidores
       ├─ MQTT activo
       ├─ ThingsBoard accesible
       └─ Métricas dentro de targets

16. generate_action_plan.py (250 líneas)
    ├─ Genera plan de acción automático
    └─ Basado en:
       ├─ Errores en logs
       ├─ Métricas fuera de target
       ├─ Alarmas activas
       └─ Estado de servicios

================================================================================
                    CONFIGURACIÓN Y PERSISTENCIA
================================================================================

BASE DE DATOS (SQLite - data/admin.db):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Tabla: meters
┌─────────────────┬──────────────┬──────────────────────────────────┐
│ Campo           │ Tipo         │ Descripción                      │
├─────────────────┼──────────────┼──────────────────────────────────┤
│ id              │ INTEGER PK   │ ID único del medidor             │
│ name            │ VARCHAR(100) │ Nombre del medidor               │
│ ip_address      │ VARCHAR(15)  │ IP del medidor                   │
│ port            │ INTEGER      │ Puerto (3333)                    │
│ client_id       │ INTEGER      │ Client SAP (1 o 16)              │
│ server_id       │ INTEGER      │ Server ID (1)                    │
│ password        │ VARCHAR(50)  │ Password DLMS                    │
│ status          │ VARCHAR(20)  │ active/inactive/error            │
│ tb_enabled      │ BOOLEAN      │ ThingsBoard habilitado           │
│ tb_host         │ VARCHAR(100) │ Host MQTT (localhost)            │
│ tb_port         │ INTEGER      │ Puerto MQTT (1884 gateway)       │
│ tb_token        │ VARCHAR(100) │ Token (NULL en gateway mode)     │
│ tb_device_name  │ VARCHAR(100) │ Nombre en ThingsBoard            │
│ last_seen       │ DATETIME     │ Última lectura exitosa           │
│ last_error      │ TEXT         │ Último error                     │
│ error_count     │ INTEGER      │ Contador de errores              │
└─────────────────┴──────────────┴──────────────────────────────────┘

Tabla: meter_metrics
┌─────────────────┬──────────────┬──────────────────────────────────┐
│ timestamp       │ DATETIME     │ Timestamp de la métrica          │
│ meter_id        │ INTEGER FK   │ ID del medidor                   │
│ success_rate    │ FLOAT        │ % de éxito                       │
│ mqtt_rate       │ FLOAT        │ % publicaciones MQTT             │
│ avg_latency     │ FLOAT        │ Latencia promedio (ms)           │
│ reconnections   │ INTEGER      │ Reconexiones en periodo          │
│ hdlc_errors     │ INTEGER      │ Errores HDLC                     │
└─────────────────┴──────────────┴──────────────────────────────────┘

Tabla: alarms
┌─────────────────┬──────────────┬──────────────────────────────────┐
│ id              │ INTEGER PK   │ ID de alarma                     │
│ meter_id        │ INTEGER FK   │ Medidor relacionado              │
│ alarm_type      │ VARCHAR(50)  │ connection_loss/hdlc_error/etc   │
│ severity        │ VARCHAR(20)  │ critical/warning/info            │
│ message         │ TEXT         │ Descripción de la alarma         │
│ created_at      │ DATETIME     │ Cuándo se creó                   │
│ resolved_at     │ DATETIME     │ Cuándo se resolvió (NULL si no)  │
└─────────────────┴──────────────┴──────────────────────────────────┘

ARCHIVOS DE CONFIGURACIÓN:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

mqtt_config.json (Legacy - no usado en multi-meter):
{
  "dlms_host": "192.168.1.128",
  "dlms_port": 3333,
  "mqtt_host": "localhost",
  "mqtt_port": 1883,
  "access_token": "...",
  "measurements": ["voltage_l1", "current_l1", ...]
}

dlms-mqtt-bridge.service (systemd):
[Unit]
Description=DLMS Multi-Meter Bridge Service
After=network.target mosquitto.service

[Service]
Type=simple
User=root
WorkingDirectory=/path/to/project
ExecStart=/usr/bin/python3 dlms_multi_meter_bridge.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target

================================================================================
                    FORMATO DE DATOS (JSON)
================================================================================

TELEMETRÍA PUBLICADA A MQTT:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Topic: v1/devices/me/telemetry
Payload:
{
  "ts": 1699734567000,           // Timestamp en milisegundos
  "values": {
    "voltage_l1": 136.5,          // Voltaje Fase A (V)
    "current_l1": 1.33,           // Corriente Fase A (A)
    "frequency": 60.0,            // Frecuencia (Hz)
    "active_power": 181.5,        // Potencia activa (W)
    "active_energy": 56281.0      // Energía acumulada (Wh)
  }
}

ATRIBUTOS PUBLICADOS A MQTT:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Topic: v1/devices/me/attributes
Payload:
{
  "meter_name": "medidor_dlms_principal",
  "ip_address": "192.168.1.128",
  "port": 3333,
  "client_sap": 1,
  "firmware_version": "1.2.3",
  "last_connection": "2025-11-11T10:30:00Z"
}

================================================================================
                    CICLO DE VIDA DE UNA LECTURA
================================================================================

1. INICIO (t=0s):
   └─ MultiMeterBridge.load_meters_from_db()
      ├─ Lee meters table de SQLite
      ├─ Para cada meter activo:
      │  ├─ Crea MeterWorker (Thread)
      │  ├─ Crea MQTT client individual
      │  └─ Inicia worker thread
      └─ Inicia monitor_loop (cada 60s)

2. WORKER THREAD (continuo):
   └─ MeterWorker.run()
      ├─ Crea DLMSProductionPoller
      │  └─ Configura QoS components
      ├─ Loop infinito:
      │  ├─ poller.poll_once()
      │  │  ├─ DLMSClient.connect()
      │  │  │  ├─ TCP socket.connect()
      │  │  │  ├─ Envía AARQ (Association Request)
      │  │  │  └─ Recibe AARE (Association Response)
      │  │  ├─ Para cada measurement:
      │  │  │  ├─ Envía COSEM GET-REQUEST
      │  │  │  ├─ Recibe COSEM GET-RESPONSE
      │  │  │  └─ Parsea valor
      │  │  └─ DLMSClient.disconnect()
      │  ├─ mqtt_client.publish_telemetry(readings)
      │  │  └─ Publica a localhost:1884 (QoS=1)
      │  ├─ Registra métricas en DB
      │  └─ sleep(1.0s) hasta siguiente lectura
      └─ Si error: Auto-recovery con backoff

3. MQTT FLOW:
   └─ Worker publica a Mosquitto (1884)
      ├─ Mosquitto recibe mensaje
      ├─ Gateway suscribe y recibe
      ├─ Gateway transforma y añade token
      ├─ Gateway publica a ThingsBoard (1883)
      └─ ThingsBoard procesa y almacena

4. THINGSBOARD:
   └─ Recibe telemetría
      ├─ Valida token de dispositivo
      ├─ Guarda en PostgreSQL
      ├─ Ejecuta Rule Engine
      │  ├─ Chequea alarmas
      │  ├─ Triggers de notificación
      │  └─ Procesamiento customizado
      └─ Actualiza Dashboard en tiempo real

5. MONITOREO (cada 60s):
   └─ MultiMeterBridge._monitor_loop()
      ├─ Lee stats de cada worker:
      │  ├─ Cycles completados
      │  ├─ Success rate
      │  ├─ MQTT messages sent
      │  └─ Network stats
      ├─ Escribe SYSTEM STATUS REPORT a logs
      └─ Actualiza meter_metrics table

6. WATCHDOGS (continuo):
   └─ DLMSProductionPoller._check_watchdogs()
      ├─ Watchdog de Silencio:
      │  └─ Si >10 min sin lecturas → Reconexión
      ├─ Watchdog HDLC:
      │  └─ Si >15 errores consecutivos → Buffer clean
      └─ Circuit Breaker:
         └─ Si >10 reconnect/hora → Pausa 5 min

================================================================================
                    COMANDOS DE OPERACIÓN DIARIA
================================================================================

VERIFICAR ESTADO:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Ver servicio
sudo systemctl status dlms-multi-meter.service

# Logs en tiempo real
sudo journalctl -u dlms-multi-meter.service -f

# Estado de medidores
python3 meter_cli.py list
python3 meter_cli.py status 1
python3 meter_cli.py status 2

# Logs de un medidor específico
python3 meter_cli.py follow 1

# Salud del sistema
python3 system_health_monitor.py --minutes 60
python3 meter_cli.py health

CONTROL DE MEDIDORES:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Test de conectividad
python3 meter_cli.py test 1
python3 meter_cli.py test 2

# Pausar/reanudar medidor
python3 meter_cli.py pause 1
python3 meter_cli.py resume 1

# Restart worker sin reiniciar servicio
python3 meter_cli.py restart 1

DIAGNÓSTICO:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Chequeo QoS completo
python3 qos_health_check.py

# Plan de acción automático
python3 generate_action_plan.py

# Ver alarmas activas
sqlite3 data/admin.db "SELECT * FROM alarms WHERE resolved_at IS NULL"

# Ver métricas recientes
sqlite3 data/admin.db "SELECT * FROM meter_metrics ORDER BY timestamp DESC LIMIT 10"

REINICIO DE SERVICIOS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Reiniciar todo el sistema
sudo systemctl restart dlms-multi-meter.service
sudo systemctl restart mosquitto
sudo systemctl restart thingsboard

# Reload config sin reiniciar
sudo systemctl reload dlms-multi-meter.service

================================================================================
                    ARQUITECTURA DE RED
================================================================================

Red Local (192.168.1.0/24):
┌────────────────────────────────────────────────────────────────────────┐
│                                                                        │
│  Router/Switch (192.168.1.1)                                          │
│         │                                                              │
│         ├─────────┬─────────────┬─────────────┬──────────────┐       │
│         │         │             │             │              │        │
│    Medidor 1  Medidor 2    Servidor      Gateway       Otros         │
│    .128:3333  .135:3333      (PCI)      .Gateway       devices       │
│         │         │             │             │              │        │
│         │         │             │             │              │        │
│         └─────────┴─────────────┴─────────────┴──────────────┘       │
│                                 │                                      │
│                          ┌──────┴──────┐                              │
│                          │             │                              │
│                    Mosquitto      ThingsBoard                         │
│                    :1884          :1883,:8080                         │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘

Localhost (127.0.0.1):
┌────────────────────────────────────────────────────────────────────────┐
│  Puerto 1884: Mosquitto (MQTT Broker)                                 │
│  Puerto 1883: ThingsBoard (MQTT Endpoint)                             │
│  Puerto 8080: ThingsBoard (Web UI)                                    │
│  Puerto 9090: ThingsBoard (RPC)                                       │
│  Puerto 5001: Meter Control API (Flask)                               │
│  Puerto 5432: PostgreSQL (ThingsBoard DB)                             │
└────────────────────────────────────────────────────────────────────────┘

================================================================================
