#!/bin/bash
#
# Script wrapper para ejecutar health monitor desde cron
# Guarda reportes y envía alertas si el sistema está en estado crítico
#

# Obtener directorio del proyecto (padre de scripts/)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$SCRIPT_DIR"

# Variables
PYTHON_BIN="/usr/bin/python3"
MONITOR_SCRIPT="system_health_monitor.py"
LOG_FILE="logs/cron_health_checks.log"
ALERT_FILE="logs/last_alert.txt"

# Crear directorio de logs si no existe
mkdir -p logs

# Timestamp
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

echo "[$TIMESTAMP] Starting health check..." >> "$LOG_FILE"

# Ejecutar monitor y capturar exit code
$PYTHON_BIN "$MONITOR_SCRIPT" --minutes 60 --save >> "$LOG_FILE" 2>&1
EXIT_CODE=$?

echo "[$TIMESTAMP] Health check completed with exit code: $EXIT_CODE" >> "$LOG_FILE"

# Interpretar exit code
# 0 = HEALTHY/WARNING
# 1 = DEGRADED
# 2 = CRITICAL
# 3 = UNKNOWN

if [ $EXIT_CODE -eq 2 ]; then
    echo "[$TIMESTAMP] ⚠️  ALERT: System is in CRITICAL state!" >> "$LOG_FILE"
    
    # Verificar si ya enviamos alerta recientemente (últimas 4 horas)
    if [ -f "$ALERT_FILE" ]; then
        LAST_ALERT=$(cat "$ALERT_FILE")
        CURRENT_TIME=$(date +%s)
        TIME_DIFF=$((CURRENT_TIME - LAST_ALERT))
        
        # 4 horas = 14400 segundos
        if [ $TIME_DIFF -lt 14400 ]; then
            echo "[$TIMESTAMP] Alert already sent recently, skipping duplicate" >> "$LOG_FILE"
            exit 0
        fi
    fi
    
    # Guardar timestamp de esta alerta
    date +%s > "$ALERT_FILE"
    
    # Aquí podrías agregar envío de email/SMS
    # Ejemplo: echo "System CRITICAL" | mail -s "DLMS Alert" admin@example.com
    
    echo "[$TIMESTAMP] Alert notification would be sent here" >> "$LOG_FILE"
    
elif [ $EXIT_CODE -eq 1 ]; then
    echo "[$TIMESTAMP] ℹ️  System is DEGRADED" >> "$LOG_FILE"
else
    echo "[$TIMESTAMP] ✅ System is HEALTHY" >> "$LOG_FILE"
fi

# Limpiar reportes antiguos (más de 7 días)
find logs/health_reports/ -name "health_report_*.json" -mtime +7 -delete 2>/dev/null
find logs/action_plans/ -name "action_plan_*.json" -mtime +7 -delete 2>/dev/null

echo "[$TIMESTAMP] Cleanup completed" >> "$LOG_FILE"
echo "----------------------------------------" >> "$LOG_FILE"

exit 0
