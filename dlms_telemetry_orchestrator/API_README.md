# 🔌 API de Control de Medidores DLMS

API REST y Cliente CLI para controlar y monitorear medidores DLMS de forma individual.

## 📋 Características

- ✅ **Monitoreo en tiempo real** de cada medidor
- ✅ **Control individual** (pausar/reanudar medidores)
- ✅ **Logs en vivo** con seguimiento en tiempo real
- ✅ **Pruebas de conexión** automáticas
- ✅ **Métricas y estadísticas** detalladas
- ✅ **API REST** completa
- ✅ **Cliente CLI** con colores

## 🚀 Inicio Rápido

### 1. Iniciar la API

```bash
# Método 1: Script automático
./start_api.sh

# Método 2: Manual
python3 meter_control_api.py
```

La API estará disponible en: **http://localhost:5001/**

### 2. Usar el Cliente CLI

```bash
# Ver todos los medidores
python3 meter_cli.py list

# Ver estado detallado del Medidor 1
python3 meter_cli.py status 1

# Ver logs del Medidor 2
python3 meter_cli.py logs 2 --lines 30

# Seguir logs en tiempo real
python3 meter_cli.py follow 1

# Estado general del sistema
python3 meter_cli.py health
```

## 📖 Comandos del CLI

### Información

| Comando | Descripción | Ejemplo |
|---------|-------------|---------|
| `list` | Lista todos los medidores | `python3 meter_cli.py list` |
| `status <id>` | Estado detallado de un medidor | `python3 meter_cli.py status 1` |
| `logs <id>` | Logs recientes | `python3 meter_cli.py logs 1 --lines 50` |
| `follow <id>` | Seguir logs en tiempo real | `python3 meter_cli.py follow 1` |
| `health` | Estado general del sistema | `python3 meter_cli.py health` |

### Control

| Comando | Descripción | Ejemplo |
|---------|-------------|---------|
| `pause <id>` | Pausar polling de un medidor | `python3 meter_cli.py pause 2` |
| `resume <id>` | Reanudar polling | `python3 meter_cli.py resume 2` |
| `test <id>` | Probar conexión (ping + TCP) | `python3 meter_cli.py test 2` |
| `restart <id>` | Reiniciar worker del medidor | `python3 meter_cli.py restart 2` |

## 🌐 API REST Endpoints

### Información de Medidores

```bash
# Listar todos los medidores
curl http://localhost:5001/api/meters

# Detalles de un medidor
curl http://localhost:5001/api/meters/1

# Estado en tiempo real
curl http://localhost:5001/api/meters/1/status

# Logs recientes
curl http://localhost:5001/api/meters/1/logs?lines=20

# Métricas históricas
curl http://localhost:5001/api/meters/1/metrics?limit=100
```

### Control de Medidores

```bash
# Pausar medidor
curl -X POST http://localhost:5001/api/meters/2/pause

# Reanudar medidor
curl -X POST http://localhost:5001/api/meters/2/resume

# Probar conexión
curl -X POST http://localhost:5001/api/meters/2/test

# Reiniciar worker
curl -X POST http://localhost:5001/api/meters/2/restart
```

### Sistema

```bash
# Estado del sistema
curl http://localhost:5001/api/system/health

# Logs del sistema
curl http://localhost:5001/api/system/logs?lines=100

# Reiniciar servicio completo
curl -X POST http://localhost:5001/api/system/service/restart
```

## 📊 Ejemplos de Uso

### Monitorear Medidor en Tiempo Real

```bash
# Terminal 1: Seguir logs
python3 meter_cli.py follow 1

# Terminal 2: Ver estado cada 5 segundos
watch -n 5 "python3 meter_cli.py status 1"
```

### Pausar Medidor Problemático

```bash
# Pausar el Medidor 2
python3 meter_cli.py pause 2

# Verificar que se pausó
python3 meter_cli.py status 2

# Cuando esté listo, reanudar
python3 meter_cli.py resume 2

# Reiniciar servicio para aplicar
sudo systemctl restart dlms-multi-meter.service
```

### Diagnosticar Problemas de Conexión

```bash
# Probar conexión completa
python3 meter_cli.py test 2

# Ver logs de errores
python3 meter_cli.py logs 2 --lines 100 | grep ERROR

# Seguir en tiempo real
python3 meter_cli.py follow 2
```

### Integración con Scripts

```bash
#!/bin/bash
# Script para verificar salud de todos los medidores

API="http://localhost:5001/api"

echo "Verificando medidores..."

# Obtener lista de medidores
METERS=$(curl -s "$API/meters" | jq -r '.meters[].id')

for meter_id in $METERS; do
    echo "Medidor $meter_id:"
    
    # Obtener estado
    STATUS=$(curl -s "$API/meters/$meter_id/status")
    SUCCESS_RATE=$(echo "$STATUS" | jq -r '.status.live_stats.success_rate')
    
    echo "  Success rate: $SUCCESS_RATE%"
    
    # Alertar si < 80%
    if (( $(echo "$SUCCESS_RATE < 80" | bc -l) )); then
        echo "  ⚠️  ALERTA: Baja tasa de éxito"
        # Enviar notificación, email, etc.
    fi
done
```

## 🔧 Configuración

### Permisos Sudo (Recomendado)

Para evitar solicitudes de password, añade a `/etc/sudoers.d/dlms-api`:

```bash
# Permitir journalctl y systemctl sin password
pci ALL=(ALL) NOPASSWD: /usr/bin/journalctl
pci ALL=(ALL) NOPASSWD: /usr/bin/systemctl status dlms-multi-meter.service
pci ALL=(ALL) NOPASSWD: /usr/bin/systemctl restart dlms-multi-meter.service
```

### Variables de Entorno

```bash
export METER_API_HOST=0.0.0.0  # Host de la API
export METER_API_PORT=5001      # Puerto de la API
export METER_DB_PATH=data/admin.db  # Ruta a la base de datos
```

## 📱 Frontend Web (Futuro)

La API está lista para conectar un frontend web. Estructura de respuestas:

```json
{
  "success": true,
  "meters": [
    {
      "id": 1,
      "name": "medidor_dlms_principal",
      "ip_address": "192.168.1.127",
      "port": 3333,
      "status": "active",
      "latest_metric": {
        "success_rate": 99.9,
        "total_reads": 1000,
        "messages_sent": 500
      }
    }
  ]
}
```

## 🐛 Troubleshooting

### API no responde

```bash
# Verificar si está corriendo
ps aux | grep meter_control_api

# Ver logs
tail -f /var/log/syslog | grep meter_control_api

# Reiniciar
pkill -f meter_control_api.py
./start_api.sh
```

### Error de permisos

```bash
# Si los comandos requieren sudo y no funcionan,
# ejecuta la API con sudo (no recomendado para producción)
sudo python3 meter_control_api.py
```

### Cliente CLI no conecta

```bash
# Verificar que la API esté corriendo
curl http://localhost:5001/api/system/health

# Si no responde, iniciar la API
./start_api.sh
```

## 📝 Notas

- La API usa Flask en modo desarrollo. Para producción, usar Gunicorn o similar.
- Los comandos de control (pause/resume) requieren reiniciar el servicio para aplicar.
- El comando `follow` actualiza cada 2 segundos.
- Los logs se obtienen de journalctl, requiere permisos sudo.

## 🔗 Archivos Relacionados

- `meter_control_api.py` - Servidor API REST
- `meter_cli.py` - Cliente CLI
- `start_api.sh` - Script de inicio
- `dlms_multi_meter_bridge.py` - Servicio principal de polling

## 📄 Licencia

Parte del proyecto DLMS Bridge
