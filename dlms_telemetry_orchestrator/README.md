# Sistema de Telemetría DLMS a ThingsBoard con Arquitectura Gateway

**Trabajo de Grado** - Ingeniería Electrónica  
**Autor:** Brayan Ricardo Pisso Ramírez  
**Universidad:** [Universidad Nacional de Colombia - Sede Manizales]  
**Año:** 2025
---

## 🎯 Objetivo

Desarrollar un sistema de telemetría IoT que permita la **adquisición, transmisión y visualización en tiempo real** de datos provenientes de medidores eléctricos DLMS/COSEM hacia la plataforma ThingsBoard, eliminando conflictos de token MQTT mediante una arquitectura Gateway de 3 capas.

---

## 📐 Alcance

### Funcionalidades Implementadas

✅ **Lectura de medidores DLMS/COSEM** vía protocolo HDLC sobre TCP/IP  
✅ **Publicación MQTT** con arquitectura Gateway para evitar conflictos  
✅ **Visualización en ThingsBoard** en tiempo real  
✅ **Soporte multi-medidor** concurrente (escalable a N dispositivos)  
✅ **Monitoreo de salud** con watchdog y circuit breaker  
✅ **Optimización de velocidad** (intervalo de 2s, ~12 lecturas/min)

### Limitaciones

- Protocolo DLMS únicamente (no Modbus/IEC)
- Medidores con conectividad TCP/IP (no serie RS485 directo)
- ThingsBoard como plataforma IoT (no otras plataformas)

---

## 🏗️ Diagrama de Arquitectura

```
┌──────────────────┐
│  Medidor DLMS    │ (192.168.1.127:3333)
│  Microstar       │ 5 mediciones: V, A, Hz, W, Wh
└────────┬─────────┘
         │ DLMS/HDLC (cada 2s)
         ↓
┌─────────────────────────────┐
│ dlms_multi_meter_bridge.py  │ (Python)
│ • Lee protocolo DLMS         │
│ • Publica MQTT sin token     │
│ • Puerto 1884 (local)        │
└────────┬────────────────────┘
         │ MQTT
         ↓
┌──────────────────┐
│ Mosquitto Broker │ (localhost)
│ • Puerto 1884    │ (local, sin auth)
│ • Puerto 1883    │ (ThingsBoard)
└────────┬─────────┘
         │
         ↓
┌──────────────────────┐
│ ThingsBoard Gateway  │ (v3.7.9)
│ • Consume 1884       │
│ • Publica 1883       │
│ • Token propio       │
└────────┬─────────────┘
         │ MQTT con token
         ↓
┌──────────────────┐
│   ThingsBoard    │ (Plataforma IoT)
│ • Dashboards     │
│ • Visualización  │
│ • Almacenamiento │
└──────────────────┘
```

**Problema resuelto:** Antes los 2 servicios (dlms-bridge y gateway) compartían el mismo token → desconexiones "code 7". Ahora cada uno usa su propio canal MQTT.

---

## 💻 Requisitos del Sistema

### Hardware

- **Servidor/PC Linux:** Ubuntu 20.04+ o similar
- **RAM:** Mínimo 2GB (recomendado 4GB)
- **Red:** Conectividad Ethernet con medidores DLMS
- **Medidor:** Compatible con DLMS/COSEM sobre TCP/IP (ej. Microstar)

### Software

| Componente | Versión | Propósito |
|------------|---------|-----------|
| Python | 3.10+ | Lenguaje principal |
| Mosquitto | 2.0+ | Broker MQTT |
| ThingsBoard Gateway | 3.7+ | Gateway IoT |
| SQLite | 3.x | Base de datos |
| systemd | - | Gestión de servicios |

### Dependencias Python

```bash
# Core
dlms-cosem==22.3.0          # Protocolo DLMS
paho-mqtt==2.1.0            # Cliente MQTT
sqlalchemy>=2.0.0           # ORM base de datos
psutil>=5.9.0               # Monitoreo de red

# Opcional (Admin)
fastapi==0.104.1            # API REST
streamlit==1.28.2           # Dashboard web
```

---

## 🚀 Cómo Ejecutar

### 1. Instalación

```bash
# Clonar repositorio
git clone https://github.com/jsebgiraldo/Tesis-app.git
cd Tesis-app/dlms-bridge

# Crear entorno virtual
python3 -m venv venv
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
```

### 2. Configurar Medidor

```bash
# Agregar medidor a la base de datos
python3 << EOF
from admin.database import Database
import sqlite3

conn = sqlite3.connect('data/admin.db')
c = conn.cursor()

# Insertar medidor
c.execute("""
    INSERT INTO meters (name, ip_address, port, tb_host, tb_port, tb_token)
    VALUES ('Medidor_01', '192.168.1.127', 3333, 'localhost', 1884, NULL)
""")

conn.commit()
conn.close()
print("✅ Medidor configurado")
EOF
```

### 3. Iniciar Sistema

```bash
# Opción A: Modo desarrollo (manual)
python3 dlms_multi_meter_bridge.py

# Opción B: Modo producción (servicio)
sudo systemctl start dlms-multi-meter.service
sudo journalctl -u dlms-multi-meter.service -f
```

### 4. Verificar Funcionamiento

```bash
# Ejecutar script de verificación
./verify_gateway_architecture.sh

# Debe mostrar:
# ✅ SISTEMA FUNCIONANDO CORRECTAMENTE
# - dlms-multi-meter: ACTIVO
# - mosquitto: ESCUCHANDO en 1884
# - thingsboard-gateway: PROCESANDO mensajes
# - CERO warnings "code 7"
```

---

## 📚 Documentación Adicional

### Documento PDF (Trabajo Escrito)

> 📄 **[Pendiente]** `docs/Trabajo_Final_Sebastian_Giraldo.pdf`  
> Documento formal con marco teórico, metodología, resultados y conclusiones.

### Documentación Técnica Generada

> 📘 **[Pendiente]** `docs/technical/`  
> Documentación técnica auto-generada del código (Sphinx/Doxygen).

### Documentos Existentes

- [Arquitectura del Sistema](docs/ARQUITECTURA_FINAL.md) - Diseño detallado
- [Guía de Producción](docs/GUIA_PRODUCCION.md) - Despliegue en servidor
- [Solución Code 7](docs/SOLUCION_GATEWAY_THINGSBOARD.md) - Arquitectura Gateway implementada
- [Implementación Exitosa](docs/IMPLEMENTACION_GATEWAY_EXITOSA.md) - Validación y métricas

---

## � Contacto

**Autor:** Sebastián Giraldo  
**Email:** [Pendiente]  
**GitHub:** [@jsebgiraldo](https://github.com/jsebgiraldo)  
**Repositorio:** [Tesis-app](https://github.com/jsebgiraldo/Tesis-app)

---

**Última actualización:** Noviembre 2025
