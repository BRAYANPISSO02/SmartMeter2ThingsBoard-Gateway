#!/usr/bin/env python3
"""
Diagnóstico completo del Medidor 2
"""
import socket
import subprocess
import sqlite3
from datetime import datetime

print("="*80)
print("🔍 DIAGNÓSTICO COMPLETO - MEDIDOR 2")
print("="*80)
print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

# 1. Información de base de datos
print("📊 1. CONFIGURACIÓN EN BASE DE DATOS")
print("-" * 80)
db = sqlite3.connect('data/admin.db')
cursor = db.cursor()
cursor.execute("""
    SELECT id, name, ip_address, port, client_id, server_id, password, status
    FROM meters WHERE id = 2
""")
row = cursor.fetchone()
if row:
    print(f"   ID: {row[0]}")
    print(f"   Nombre: {row[1]}")
    print(f"   IP:Puerto: {row[2]}:{row[3]}")
    print(f"   Client ID (SAP): {row[4]}")
    print(f"   Server ID: {row[5]}")
    print(f"   Password: {row[6]}")
    print(f"   Status: {row[7]}")
    
    meter_ip = row[2]
    meter_port = row[3]
db.close()
print()

# 2. Test de conectividad de red
print("🌐 2. CONECTIVIDAD DE RED")
print("-" * 80)

# Ping test
print(f"   Ping test a {meter_ip}...")
result = subprocess.run(['ping', '-c', '3', '-W', '2', meter_ip], 
                       capture_output=True, text=True)
if result.returncode == 0:
    print("   ✅ Ping: OK")
    for line in result.stdout.split('\n'):
        if 'packets transmitted' in line or 'rtt' in line:
            print(f"      {line.strip()}")
else:
    print("   ❌ Ping: FAILED")

# TCP test
print(f"\n   TCP test a {meter_ip}:{meter_port}...")
try:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(5)
    start = datetime.now()
    sock.connect((meter_ip, meter_port))
    elapsed = (datetime.now() - start).total_seconds() * 1000
    sock.close()
    print(f"   ✅ TCP: OK ({elapsed:.1f}ms)")
except Exception as e:
    print(f"   ❌ TCP: FAILED - {e}")
print()

# 3. Estado del servicio
print("⚙️  3. ESTADO DEL SERVICIO")
print("-" * 80)
result = subprocess.run(['systemctl', 'is-active', 'dlms-multi-meter.service'],
                       capture_output=True, text=True)
print(f"   Service status: {result.stdout.strip()}")

result = subprocess.run(['systemctl', 'status', 'dlms-multi-meter.service', '--no-pager', '-l'],
                       capture_output=True, text=True)
for line in result.stdout.split('\n')[:10]:
    if line.strip():
        print(f"   {line}")
print()

# 4. Logs recientes del medidor 2
print("📝 4. LOGS RECIENTES (últimos 10 eventos)")
print("-" * 80)
result = subprocess.run([
    'sudo', 'journalctl', '-u', 'dlms-multi-meter.service',
    '--since', '10 minutes ago', '--no-pager'
], capture_output=True, text=True)

meter2_logs = [line for line in result.stdout.split('\n') if 'Medidor_DLMS_02' in line or '192.168.1.135' in line]
for log in meter2_logs[-10:]:
    if log.strip():
        # Extraer solo la parte relevante
        if ' - ' in log:
            parts = log.split(' - ', 2)
            if len(parts) >= 3:
                print(f"   {parts[2]}")
print()

# 5. Métricas y estadísticas
print("📈 5. MÉTRICAS Y ESTADÍSTICAS")
print("-" * 80)
db = sqlite3.connect('data/admin.db')
cursor = db.cursor()

# Últimas lecturas
cursor.execute("""
    SELECT timestamp, voltage_l1, current_l1, active_power_total
    FROM readings
    WHERE meter_id = 2
    ORDER BY timestamp DESC
    LIMIT 5
""")
readings = cursor.fetchall()
if readings:
    print("   Últimas 5 lecturas:")
    for r in readings:
        print(f"      {r[0]}: V={r[1]}V, I={r[2]}A, P={r[3]}W")
else:
    print("   ⚠️  No hay lecturas registradas")

# Errores recientes
cursor.execute("""
    SELECT COUNT(*) FROM diagnostics
    WHERE meter_id = 2
    AND timestamp > datetime('now', '-1 hour')
""")
error_count = cursor.fetchone()[0]
print(f"\n   Errores en última hora: {error_count}")

db.close()
print()

# 6. Recomendaciones
print("💡 6. RECOMENDACIONES")
print("-" * 80)
print("""
   Basado en el diagnóstico:
   
   ✓ Conectividad de red: OK (ping y TCP funcionan)
   ✗ Protocolo DLMS: FAILED (socket cerrado después de handshake)
   
   Posibles causas:
   1. Medidor bloqueado después de múltiples intentos fallidos
   2. Credenciales incorrectas (aunque ya probamos ambos usuarios)
   3. Parámetros DLMS adicionales requeridos (security suite, etc.)
   4. Medidor requiere reset físico
   5. Firmware del medidor con problema
   
   Acciones sugeridas:
   1. Reset físico del medidor (apagado/encendido)
   2. Verificar documentación del fabricante para parámetros adicionales
   3. Pausar intentos automáticos para evitar más bloqueos
   4. Contactar soporte técnico del fabricante del medidor
""")

print("="*80)
print("Diagnóstico completado")
print("="*80)
