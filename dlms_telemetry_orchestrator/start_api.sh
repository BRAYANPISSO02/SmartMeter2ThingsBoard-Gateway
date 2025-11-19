#!/bin/bash
# Script para iniciar la API de control de medidores
# Requiere que el usuario tenga permisos sudo sin password para systemctl y journalctl

cd /home/pci/Documents/sebas_giraldo/Tesis-app/dlms-bridge

echo "🚀 Iniciando Meter Control API..."
python3 meter_control_api.py &

API_PID=$!
echo "✅ API iniciada con PID: $API_PID"
echo "$API_PID" > /tmp/meter_control_api.pid
echo ""
echo "📖 Documentación: http://localhost:5001/"
echo "🛑 Para detener: kill $API_PID"
echo ""
echo "Ejemplos de uso del CLI:"
echo "  python3 meter_cli.py list"
echo "  python3 meter_cli.py status 1"
echo "  python3 meter_cli.py logs 1 --lines 20"
echo "  python3 meter_cli.py follow 1"
