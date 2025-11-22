# SmartMeter2ThingsBoard-Gateway

## Sistema Integral de Telemetría IoT para Medidores Inteligentes DLMS/COSEM

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/docker-20.10%2B-blue.svg)](https://www.docker.com/)
[![ThingsBoard](https://img.shields.io/badge/ThingsBoard-4.2.1-orange.svg)](https://thingsboard.io/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

---

## 📄 Información del Proyecto

**Proyecto de Grado** - Ingeniería Electrónica  
**Universidad:** Universidad Nacional de Colombia - Sede Manizales  
**Autor:** Brayan Ricardo Pisso Ramírez  
**Director:** Gustavo Adolfo Osorio Londoño  
**Año:** 2025

---

## 📖 Tabla de Contenidos

- [Descripción General](#-descripción-general)
- [Características Principales](#-características-principales)
- [Arquitectura del Sistema](#-arquitectura-del-sistema)
- [Componentes del Proyecto](#-componentes-del-proyecto)
- [Requisitos del Sistema](#-requisitos-del-sistema)
- [Guía de Instalación Rápida](#-guía-de-instalación-rápida)
- [Estructura del Repositorio](#-estructura-del-repositorio)
- [Documentación Detallada](#-documentación-detallada)
- [Casos de Uso](#-casos-de-uso)
- [Contribuciones](#-contribuciones)
- [Licencia](#-licencia)
- [Referencias](#-referencias)

---

## 🎯 Descripción General

**SmartMeter2ThingsBoard-Gateway** es una solución integral de telemetría IoT de extremo a extremo que conecta medidores inteligentes basados en el protocolo **DLMS/COSEM** con la plataforma **ThingsBoard IoT** para el monitoreo, almacenamiento y visualización en tiempo real de variables eléctricas críticas.

Este sistema permite la transformación digital de infraestructuras de medición eléctrica tradicionales, habilitando capacidades de:
- 📊 **Monitoreo remoto en tiempo real** de variables eléctricas
- 🔄 **Gestión simultánea de múltiples medidores** con arquitectura escalable
- 📈 **Análisis histórico** de consumo y parámetros eléctricos
- 🚨 **Generación automática de alarmas** ante condiciones anormales
- 📱 **Visualización intuitiva** mediante dashboards web personalizables
- 🔐 **Comunicación segura** con soporte SSL/TLS

### Variables Monitoreadas

El sistema captura y transmite las siguientes variables eléctricas:

| Variable | Unidad | Descripción |
|----------|--------|-------------|
| Voltaje (L1, L2, L3) | V | Voltaje por fase |
| Corriente (L1, L2, L3) | A | Corriente por fase |
| Frecuencia | Hz | Frecuencia de la red |
| Potencia Activa | W | Potencia instantánea |
| Energía Activa | Wh | Energía acumulada |

---

## ✨ Características Principales

### Sistema de Adquisición de Datos (DLMS)

- ✅ **Protocolo DLMS/COSEM** - Implementación completa del estándar IEC 62056
- ✅ **Multi-medidor concurrente** - Gestión simultánea de múltiples dispositivos
- ✅ **Auto-recuperación inteligente** - 3 niveles de recuperación ante fallos
- ✅ **Alta disponibilidad** - Circuit breaker para prevención de loops
- ✅ **Optimización de rendimiento** - Caché de scalers para lecturas más rápidas
- ✅ **QoS nivel 1** - Garantía de entrega de mensajes MQTT

### Plataforma de Visualización (ThingsBoard)

- ✅ **Infraestructura contenedorizada** - Despliegue con Docker Compose
- ✅ **Multi-protocolo** - Soporte para MQTT, HTTP, CoAP/LwM2M
- ✅ **Base de datos time-series** - PostgreSQL 16 para almacenamiento eficiente
- ✅ **Procesamiento de eventos** - Apache Kafka para mensajería asíncrona
- ✅ **Dashboards personalizables** - Interfaz web intuitiva
- ✅ **API REST completa** - Integración con sistemas externos

### Gestión y Monitoreo

- ✅ **Base de datos SQLite** - Configuración centralizada de medidores
- ✅ **CLI de administración** - Herramientas de línea de comandos
- ✅ **Sistema de logs estructurados** - Trazabilidad completa
- ✅ **Métricas de rendimiento** - Tasas de éxito, uptime, latencias
- ✅ **Generación de alarmas** - Notificaciones automáticas de eventos

---

## 🏗️ Arquitectura del Sistema

### Diagrama de Arquitectura Completa

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                          CAPA FÍSICA - MEDIDORES                             │
│                                                                              │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐        │
│  │ Medidor DLMS #1 │    │ Medidor DLMS #2 │    │ Medidor DLMS #N │        │
│  │ 192.168.1.128   │    │ 192.168.1.129   │    │ 192.168.1.XXX   │        │
│  │ Puerto: 3333    │    │ Puerto: 3333    │    │ Puerto: 3333    │        │
│  └────────┬────────┘    └────────┬────────┘    └────────┬────────┘        │
└───────────┼──────────────────────┼──────────────────────┼──────────────────┘
            │                      │                      │
            │ DLMS/COSEM over TCP/IP (Protocolo IEC 62056)│
            │                      │                      │
┌───────────▼──────────────────────▼──────────────────────▼──────────────────┐
│              CAPA DE ADQUISICIÓN - DLMS TELEMETRY ORCHESTRATOR             │
│                          (Python Application)                               │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │              dlms_multi_meter_bridge.py (Orquestador)              │    │
│  │                 • Gestión de múltiples workers                     │    │
│  │                 • Auto-recuperación multinivel                     │    │
│  │                 • Monitoreo de salud del sistema                   │    │
│  └────────────────────────────┬───────────────────────────────────────┘    │
│                               │                                             │
│  ┌───────────────────┐  ┌─────┴──────┐  ┌───────────────────┐            │
│  │  MeterWorker #1   │  │ Workers    │  │  MeterWorker #N   │            │
│  │  ┌─────────────┐  │  │ Pool       │  │  ┌─────────────┐  │            │
│  │  │ DLMS Poller │  │  │ (Asyncio)  │  │  │ DLMS Poller │  │            │
│  │  │   Reader    │◄─┼──┤            ├──►  │   Reader    │  │            │
│  │  └──────┬──────┘  │  └────────────┘  │  └──────┬──────┘  │            │
│  │         │         │                   │         │         │            │
│  │  ┌──────▼──────┐  │                   │  ┌──────▼──────┐  │            │
│  │  │MQTT Publisher│  │                   │  │MQTT Publisher│  │            │
│  │  │  (QoS=1)    │  │                   │  │  (QoS=1)    │  │            │
│  │  └──────┬──────┘  │                   │  └──────┬──────┘  │            │
│  └─────────┼─────────┘                   └─────────┼─────────┘            │
│            │                                       │                       │
│            └───────────────────┬───────────────────┘                       │
│                                │ JSON Telemetry                            │
│                      ┌─────────▼─────────┐                                 │
│                      │  SQLite Database  │                                 │
│                      │  • Configuración  │                                 │
│                      │  • Métricas       │                                 │
│                      │  • Alarmas        │                                 │
│                      └───────────────────┘                                 │
│                                                                              │
└──────────────────────────────┬───────────────────────────────────────────────┘
                               │
                               │ MQTT Protocol (QoS=1)
                               │ Topic: v1/devices/+/telemetry
                               │
┌──────────────────────────────▼───────────────────────────────────────────────┐
│                  CAPA DE PLATAFORMA IoT - THINGSBOARD CE                     │
│                        (Docker Compose Stack)                                │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │                    ThingsBoard CE 4.2.1                            │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐   │    │
│  │  │ MQTT Broker  │  │ HTTP Server  │  │  Rule Engine         │   │    │
│  │  │ (Puerto 1883)│  │ (Puerto 8080)│  │  • Procesamiento     │   │    │
│  │  └──────┬───────┘  └──────┬───────┘  │  • Transformación    │   │    │
│  │         │                 │          │  • Alarmas           │   │    │
│  │         └────────┬────────┘          └──────────┬───────────┘   │    │
│  │                  ▼                              ▼               │    │
│  │         ┌────────────────┐          ┌────────────────────┐    │    │
│  │         │   Telemetry    │          │    Web UI          │    │    │
│  │         │   Processing   │          │  • Dashboards      │    │    │
│  │         └────────┬───────┘          │  • Widgets         │    │    │
│  │                  │                  │  • Device Mgmt     │    │    │
│  │                  │                  └────────────────────┘    │    │
│  └──────────────────┼───────────────────────────────────────────────┘    │
│                     │                                                     │
│                     ▼                                                     │
│  ┌────────────────────────────────┐        ┌──────────────────────┐    │
│  │   Apache Kafka 4.0 (KRaft)     │◄──────►│  PostgreSQL 16       │    │
│  │   Sistema de Mensajería        │        │  Base de Datos       │    │
│  │   • Cola de eventos            │        │  • Time-series       │    │
│  │   • Procesamiento asíncrono    │        │  • Metadatos         │    │
│  │   • Alta disponibilidad        │        │  • Configuración     │    │
│  └────────────────────────────────┘        └──────────────────────┘    │
│                                                                           │
└───────────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
                    ┌─────────────────────────────┐
                    │  USUARIOS FINALES           │
                    │  • Navegadores Web          │
                    │  • Aplicaciones Móviles     │
                    │  • APIs de Integración      │
                    └─────────────────────────────┘
```

### Flujo de Datos

1. **Adquisición (DLMS Layer)**
   - Conexión TCP/IP a medidores DLMS/COSEM
   - Lectura de códigos OBIS estándar
   - Procesamiento y normalización de datos

2. **Transmisión (MQTT Layer)**
   - Formateo de datos a JSON
   - Publicación con QoS nivel 1
   - Garantía de entrega at-least-once

3. **Procesamiento (ThingsBoard)**
   - Recepción vía MQTT broker
   - Procesamiento mediante Rule Engine
   - Almacenamiento en base de datos time-series

4. **Visualización (Web UI)**
   - Dashboards personalizables
   - Gráficos en tiempo real
   - Análisis histórico
   - Generación de reportes

---

## 🧩 Componentes del Proyecto

El sistema está compuesto por dos módulos principales independientes pero complementarios:

### 1. DLMS Telemetry Orchestrator

**Ubicación:** `/dlms_telemetry_orchestrator/`

Sistema de adquisición de datos que implementa:
- Cliente DLMS/COSEM completo
- Gestión multi-medidor concurrente
- Sistema de auto-recuperación de 3 niveles
- Publicación MQTT optimizada
- Base de datos SQLite para configuración
- CLI y API REST para administración

**Tecnologías:**
- Python 3.10+
- dlms-cosem 22.3.0
- paho-mqtt 2.0+
- SQLAlchemy 2.0+
- asyncio para concurrencia

**[Ver documentación completa →](dlms_telemetry_orchestrator/README.md)**

### 2. ThingsBoard Telemetry Docker

**Ubicación:** `/thingsboard_telemetry_docker/`

Plataforma de infraestructura IoT que proporciona:
- ThingsBoard Community Edition 4.2.1
- PostgreSQL 16 para almacenamiento
- Apache Kafka 4.0 para mensajería
- Soporte multi-protocolo (MQTT, HTTP, CoAP)
- Dashboards y widgets personalizables
- Sistema de reglas y alarmas

**Tecnologías:**
- Docker & Docker Compose
- ThingsBoard CE 4.2.1
- PostgreSQL 16
- Apache Kafka 4.0
- Nginx (opcional, para SSL/TLS)

**[Ver documentación completa →](thingsboard_telemetry_docker/README.md)**

---

## 💻 Requisitos del Sistema

### Hardware Mínimo

| Componente | Especificación Mínima | Recomendado |
|------------|----------------------|-------------|
| Procesador | Intel/AMD x64 2 cores o ARM | 4+ cores |
| RAM        | 4 GB | 8 GB |
| Almacenamiento | 20 GB disponibles | 50 GB SSD |
| Red | Ethernet 100 Mbps | Gigabit Ethernet |

### Software Requerido

| Software | Versión Mínima | Propósito |
|----------|---------------|-----------|
| Sistema Operativo | Ubuntu 20.04+ / Debian 11+ | Sistema base |
| Python | 3.10 - 3.12 | DLMS Orchestrator |
| Docker Engine | 20.10+ | ThingsBoard Stack |
| Docker Compose | 2.0+ | Orquestación de contenedores |
| Git | 2.x | Control de versiones |

### Conectividad de Red

**Puertos requeridos:**
- `3333/TCP` - Comunicación con medidores DLMS
- `1883/TCP` - MQTT (no cifrado)
- `8080/TCP` - ThingsBoard Web UI
- `8883/TCP` - MQTT sobre SSL/TLS (opcional)
- `5432/TCP` - PostgreSQL (interno)
- `9092/TCP` - Kafka (interno)

---

## 🚀 Guía de Instalación Rápida

### Pre-requisitos

1. **Instalar Docker y Docker Compose:**

```bash
# Ubuntu/Debian
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
newgrp docker
```

2. **Instalar Python 3.10+:**

```bash
sudo apt update
sudo apt install -y python3.10 python3.10-venv python3-pip
```

3. **Clonar el repositorio:**

```bash
git clone https://github.com/BRAYANPISSO02/SmartMeter2ThingsBoard-Gateway.git
cd SmartMeter2ThingsBoard-Gateway
```

### Instalación del Sistema Completo

#### Paso 1: Configurar ThingsBoard (Plataforma IoT)

```bash
# Navegar al módulo de ThingsBoard
cd thingsboard_telemetry_docker/thingsboard_telemetry_visualization

# Dar permisos de ejecución
chmod +x *.sh

# Iniciar servicios
./up.sh

# Inicializar base de datos (solo primera vez)
./install.sh

# Verificar que está corriendo
./status.sh
```

Acceder a la interfaz web: http://localhost:8080

**Credenciales por defecto:**
- Usuario: `tenant@thingsboard.org`
- Contraseña: `tenant`

#### Paso 2: Crear Dispositivo en ThingsBoard

1. Ingresar a ThingsBoard Web UI
2. Ir a **Devices** → **Add Device**
3. Crear dispositivo (ej: "Medidor_Principal")
4. **Copiar el Access Token** generado

#### Paso 3: Configurar DLMS Orchestrator

```bash
# Volver al directorio raíz
cd ../../dlms_telemetry_orchestrator

# Crear entorno virtual
python3 -m venv venv
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt

# Configurar medidor (editar con tus datos)
nano crear_medidor.py
```

Ejemplo de configuración en `crear_medidor.py`:

```python
import sqlite3

conn = sqlite3.connect('data/admin.db')
cursor = conn.cursor()

cursor.execute("""
    INSERT INTO meters (
        name, ip_address, port, 
        client_id, server_id, password,
        status, tb_enabled, tb_host, tb_port, tb_token
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
""", (
    'Medidor_Principal',           # Nombre
    '192.168.1.128',               # IP del medidor
    3333,                          # Puerto
    1,                             # Client ID
    1,                             # Server ID
    '00000000',                    # Password DLMS
    'active',                      # Estado
    1,                             # ThingsBoard habilitado
    'localhost',                   # Host ThingsBoard
    1883,                          # Puerto MQTT
    'TU_TOKEN_DE_THINGSBOARD'      # 👈 Token copiado en Paso 2
))

conn.commit()
conn.close()
print("✅ Medidor configurado")
```

Ejecutar:
```bash
python3 crear_medidor.py
```

#### Paso 4: Iniciar DLMS Orchestrator

```bash
# Verificar configuración
python3 meter_cli.py list

# Iniciar sistema
python3 dlms_multi_meter_bridge.py
```

**Salida esperada:**
```
2025-11-21 10:30:45 - [MultiMeterBridge] - INFO - Starting DLMS Multi-Meter Bridge
2025-11-21 10:30:45 - [MultiMeterBridge] - INFO - Found 1 active meters
2025-11-21 10:30:46 - [Meter[1:Medidor_Principal]] - INFO - ✓ DLMS connection established
2025-11-21 10:30:46 - [Meter[1:Medidor_Principal]] - INFO - ✓ MQTT Connected
2025-11-21 10:30:47 - [Meter[1:Medidor_Principal]] - INFO - ✓ Telemetry sent
```

#### Paso 5: Verificar Datos en ThingsBoard

1. Ir a ThingsBoard Web UI
2. Seleccionar el dispositivo creado
3. Ir a **Latest Telemetry**
4. Deberías ver las variables llegando en tiempo real:
   - voltage_l1
   - current_l1
   - frequency
   - active_power
   - active_energy

**¡Sistema funcionando! 🎉**

---

## 📁 Estructura del Repositorio

```
SmartMeter2ThingsBoard-Gateway/
│
├── README.md                          # 📖 Este archivo (documentación principal)
│
├── dlms_telemetry_orchestrator/       # 🔌 Módulo de adquisición DLMS
│   ├── README.md                      # Documentación del orquestador
│   ├── dlms_multi_meter_bridge.py     # ⭐ Script principal
│   ├── dlms_poller_production.py      # Cliente DLMS optimizado
│   ├── tb_mqtt_client.py              # Cliente MQTT para ThingsBoard
│   ├── meter_cli.py                   # CLI de administración
│   ├── requirements.txt               # Dependencias Python
│   │
│   ├── admin/                         # Módulo de administración
│   │   ├── database.py               # ORM SQLAlchemy
│   │   ├── api.py                    # API REST FastAPI
│   │   └── dashboard.py              # Dashboard Streamlit
│   │
│   ├── config/                        # Configuraciones
│   ├── data/                          # Base de datos SQLite
│   ├── logs/                          # Archivos de log
│   └── docs/                          # Documentación técnica
│
├── thingsboard_telemetry_docker/      # 🐳 Módulo de plataforma IoT
│   ├── README.md                      # Documentación de ThingsBoard
│   │
│   └── thingsboard_telemetry_visualization/
│       ├── docker-compose.yml         # ⭐ Configuración de servicios
│       ├── up.sh                      # Script de inicio
│       ├── down.sh                    # Script de detención
│       ├── install.sh                 # Inicialización de BD
│       ├── logs.sh                    # Ver logs
│       ├── status.sh                  # Ver estado
│       ├── reset.sh                   # Reinicio completo
│       └── certs/                     # Certificados SSL/TLS
│
└── gateway/                           # ⚙️ ThingsBoard Gateway (opcional)
    ├── README.md                      # Documentación del gateway
    ├── config/                        # Configuraciones de conectores
    │   ├── dlms_connector.json       # Configuración DLMS
    │   └── tb_gateway.yaml           # Configuración principal
    └── connectors/                    # Conectores personalizados
```

---

## 📚 Documentación Detallada

Cada módulo cuenta con documentación específica y detallada:

### Documentación por Módulo

| Módulo | Documento | Descripción |
|--------|-----------|-------------|
| **DLMS Orchestrator** | [dlms_telemetry_orchestrator/README.md](dlms_telemetry_orchestrator/README.md) | Instalación, configuración, uso del orquestador DLMS |
| **ThingsBoard Docker** | [thingsboard_telemetry_docker/README.md](thingsboard_telemetry_docker/README.md) | Despliegue, gestión y operación de ThingsBoard |
| **Gateway (Opcional)** | [gateway/README.md](gateway/README.md) | Configuración alternativa usando ThingsBoard Gateway |

### Documentación Técnica Adicional

| Documento | Ubicación | Contenido |
|-----------|-----------|-----------|
| Arquitectura Completa | `dlms_telemetry_orchestrator/docs/ARQUITECTURA_COMPLETA.md` | Diseño detallado del sistema |
| Guía de Producción | `dlms_telemetry_orchestrator/docs/GUIA_PRODUCCION.md` | Despliegue en entornos productivos |
| Protocolo DLMS/COSEM | `dlms_telemetry_orchestrator/docs/MICROSTAR_PROTOCOL_SPECS.md` | Especificaciones del protocolo |
| Implementación QoS | `dlms_telemetry_orchestrator/docs/QOS_IMPLEMENTATION_REPORT.md` | Sistema de calidad de servicio |
| Robustez ante Apagones | `dlms_telemetry_orchestrator/docs/ROBUSTEZ_APAGONES.md` | Estrategias de recuperación |

---

## 💡 Casos de Uso

### Caso de Uso 1: Monitoreo Residencial

**Escenario:** Casa inteligente con medidor DLMS  
**Solución:** Visualización en tiempo real de consumo eléctrico  
**Beneficios:**
- Identificación de picos de consumo
- Optimización de uso de energía
- Detección de anomalías

### Caso de Uso 2: Planta Industrial

**Escenario:** Fábrica con múltiples puntos de medición  
**Solución:** 10+ medidores gestionados concurrentemente  
**Beneficios:**
- Monitoreo centralizado
- Análisis comparativo entre áreas
- Alarmas automáticas ante sobrecargas

### Caso de Uso 3: Empresa Distribuidora

**Escenario:** Gestión de red de distribución eléctrica  
**Solución:** Sistema escalable para cientos de medidores  
**Beneficios:**
- Detección de pérdidas no técnicas
- Facturación automatizada
- Gestión de demanda

### Caso de Uso 4: Investigación Académica

**Escenario:** Análisis de calidad de energía eléctrica  
**Solución:** Almacenamiento histórico de variables eléctricas  
**Beneficios:**
- Dataset completo para análisis
- Identificación de patrones
- Validación de modelos

---

## 🤝 Contribuciones

Este proyecto es parte de un trabajo de grado. Las contribuciones son bienvenidas siguiendo estas directrices:

### Cómo Contribuir

1. **Fork** el repositorio
2. Crear una **rama** para tu feature (`git checkout -b feature/AmazingFeature`)
3. **Commit** tus cambios (`git commit -m 'Add AmazingFeature'`)
4. **Push** a la rama (`git push origin feature/AmazingFeature`)
5. Abrir un **Pull Request**

### Áreas de Contribución

- 🐛 Reporte de bugs
- 💡 Nuevas funcionalidades
- 📖 Mejoras en documentación
- 🧪 Casos de prueba
- 🌐 Traducciones
- 🎨 Mejoras en dashboards

---

## 📜 Licencia

Este proyecto está bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para más detalles.

```
Copyright (c) 2025 Brayan Ricardo Pisso Ramírez

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
```

---

## 📚 Referencias

### Estándares y Protocolos

- [DLMS User Association](https://www.dlms.com/) - Documentación oficial DLMS/COSEM
- [IEC 62056 Standard](https://webstore.iec.ch/publication/6396) - Estándar internacional
- [MQTT Protocol v3.1.1](https://docs.oasis-open.org/mqtt/mqtt/v3.1.1/mqtt-v3.1.1.html) - Especificación MQTT
- [ThingsBoard Documentation](https://thingsboard.io/docs/) - Documentación oficial

### Bibliotecas y Frameworks

- [dlms-cosem (Python)](https://github.com/pwitab/dlms-cosem) - Cliente DLMS/COSEM
- [Eclipse Paho MQTT](https://www.eclipse.org/paho/) - Cliente MQTT
- [SQLAlchemy](https://www.sqlalchemy.org/) - ORM Python
- [Docker Documentation](https://docs.docker.com/) - Documentación de Docker

### Recursos Académicos

- *"DLMS/COSEM Architecture and Protocols"* - DLMS UA
- *"IoT Platforms for Smart Grid Applications"* - IEEE
- *"Time-Series Databases for IoT Applications"* - ACM

---

## 👥 Autor y Contacto

### Autor

**Brayan Ricardo Pisso Ramírez**  
Estudiante de Ingeniería Electrónica  
Universidad Nacional de Colombia - Sede Manizales

- 📧 Email: brpissor@unal.edu.co
- 🐙 GitHub: [@BRAYANPISSO02](https://github.com/BRAYANPISSO02)
- 💼 LinkedIn: [Brayan Pisso](https://linkedin.com/in/brayan-pisso)

### Director de Tesis

**Gustavo Adolfo Osorio Londoño**  
Profesor Asociado  
Universidad Nacional de Colombia - Sede Manizales

---

## 🙏 Agradecimientos

- **Universidad Nacional de Colombia** - Por el apoyo institucional y recursos
- **Prof. Gustavo Osorio** - Por la dirección y asesoría del proyecto
- **Comunidad Open Source** - Por las excelentes herramientas y librerías
- **ThingsBoard Team** - Por la plataforma IoT robusta y bien documentada
- **DLMS User Association** - Por el estándar y la documentación técnica

---

## 📊 Estado del Proyecto

![Status](https://img.shields.io/badge/status-active-success.svg)
![Build](https://img.shields.io/badge/build-passing-brightgreen.svg)
![Coverage](https://img.shields.io/badge/coverage-85%25-green.svg)
![Version](https://img.shields.io/badge/version-2.2.0-blue.svg)

**Versión Actual:** 2.2.0  
**Última Actualización:** 21 de Noviembre de 2025  
**Estado:** ✅ Producción - Estable

### Roadmap Futuro

- [ ] Soporte para protocolo Modbus RTU/TCP
- [ ] Integración con AWS IoT Core
- [ ] Dashboard móvil (Flutter)
- [ ] Machine Learning para predicción de consumo
- [ ] API GraphQL
- [ ] Soporte para múltiples tenants

---

<div align="center">

**[⬆ Volver arriba](#smartmeter2thingsboard-gateway)**

---

*Desarrollado con ❤️ en la Universidad Nacional de Colombia*

</div>
