# SmartMeter2ThingsBoard Gateway

SmartMeter2ThingsBoard Gateway is an end-to-end telemetry solution that connects DLMS/COSEM-based meters to the ThingsBoard IoT platform for real-time monitoring, storage and visualization of electrical variables (voltage, current, power, frequency, energy, etc.).

The system is composed of two main components:

- **DLMS Telemetry Orchestrator** – Python-based client that reads DLMS/COSEM meters over TCP, handles multi-meter polling with QoS and fault tolerance, and publishes normalized JSON telemetry to a local MQTT broker.
- **ThingsBoard Telemetry Docker Stack** – Docker-based deployment of ThingsBoard CE (plus PostgreSQL and Kafka) and Python tools to configure devices, relations, GPS locations and dashboards for visualization.

This repository groups both components as a single, integrated project (bachelor’s thesis / graduation project).

---

## High-Level Architecture

End-to-end data path:

```text
DLMS Meter (TCP/3333)
    ↓
DLMS Telemetry Orchestrator (Python DLMS/COSEM client + poller)
    ↓  JSON telemetry
Local MQTT Broker (Mosquitto, e.g. :1884)
    ↓
MQTT Gateway to ThingsBoard (MQTT :1883 + token)
    ↓
ThingsBoard CE (Docker stack: ThingsBoard + PostgreSQL + Kafka)
    ↓
Dashboards & Assets (web UI on :8080)
