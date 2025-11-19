#!/usr/bin/env python3
"""
API REST para Control y Monitoreo de Medidores DLMS
Permite gestionar medidores individuales, ver su estado, logs, y controlarlos.

Endpoints:
  GET  /api/meters                    - Lista todos los medidores
  GET  /api/meters/<id>               - Detalles de un medidor específico
  GET  /api/meters/<id>/status        - Estado actual del medidor
  GET  /api/meters/<id>/logs          - Logs recientes del medidor
  GET  /api/meters/<id>/metrics       - Métricas del medidor
  POST /api/meters/<id>/pause         - Pausar polling de un medidor
  POST /api/meters/<id>/resume        - Reanudar polling de un medidor
  POST /api/meters/<id>/restart       - Reiniciar worker de un medidor
  POST /api/meters/<id>/test          - Probar conexión de un medidor
  GET  /api/system/health             - Estado general del sistema
  GET  /api/system/logs               - Logs del sistema

Usage:
  # Iniciar servidor
  python3 meter_control_api.py
  
  # Consultas
  curl http://localhost:5001/api/meters
  curl http://localhost:5001/api/meters/1/status
  
  # Control
  curl -X POST http://localhost:5001/api/meters/2/pause
  curl -X POST http://localhost:5001/api/meters/2/resume
"""

from flask import Flask, jsonify, request, Response
from flask_cors import CORS
import subprocess
import json
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging
import sys
import os

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Permitir CORS para acceso desde frontend

# Configuración
DB_PATH = 'data/admin.db'
SERVICE_NAME = 'dlms-multi-meter.service'

# ============================================================================
# UTILIDADES
# ============================================================================

def get_db_connection():
    """Obtiene conexión a la base de datos."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def get_journalctl_logs(service: str, lines: int = 100, since: str = None) -> List[str]:
    """Obtiene logs del servicio usando journalctl."""
    cmd = ['sudo', 'journalctl', '-u', service, '-n', str(lines), '--no-pager']
    if since:
        cmd.extend(['--since', since])
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        return result.stdout.split('\n')
    except Exception as e:
        logger.error(f"Error obteniendo logs: {e}")
        return []

def get_meter_logs(meter_id: int, lines: int = 50) -> List[Dict]:
    """Extrae logs específicos de un medidor."""
    logs = get_journalctl_logs(SERVICE_NAME, lines=500)
    
    # Filtrar logs del medidor específico
    meter_logs = []
    for line in logs:
        if f'Meter[{meter_id}' in line or f'medidor_dlms_principal' in line and meter_id == 1:
            # Parsear línea de log
            try:
                parts = line.split(' - ', 3)
                if len(parts) >= 4:
                    timestamp = ' '.join(parts[0].split()[:3])
                    level = parts[2] if len(parts) > 2 else 'INFO'
                    message = parts[3] if len(parts) > 3 else line
                    
                    meter_logs.append({
                        'timestamp': timestamp,
                        'level': level,
                        'message': message.strip()
                    })
            except:
                meter_logs.append({
                    'timestamp': '',
                    'level': 'INFO',
                    'message': line
                })
    
    return meter_logs[-lines:]

def get_service_status() -> Dict:
    """Obtiene el estado del servicio systemd."""
    try:
        result = subprocess.run(
            ['sudo', 'systemctl', 'status', SERVICE_NAME],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        active = 'active (running)' in result.stdout
        since_match = None
        
        for line in result.stdout.split('\n'):
            if 'Active:' in line:
                if 'since' in line:
                    since_match = line.split('since')[1].split(';')[0].strip()
        
        return {
            'active': active,
            'status': 'running' if active else 'stopped',
            'since': since_match
        }
    except Exception as e:
        logger.error(f"Error obteniendo estado del servicio: {e}")
        return {'active': False, 'status': 'unknown', 'since': None}

# ============================================================================
# ENDPOINTS - INFORMACIÓN DE MEDIDORES
# ============================================================================

@app.route('/api/meters', methods=['GET'])
def get_meters():
    """Lista todos los medidores configurados."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                id, name, ip_address, port, 
                status, client_id, server_id,
                last_seen, last_error, error_count,
                model, serial_number, firmware_version,
                created_at, updated_at
            FROM meters
            ORDER BY id
        ''')
        
        meters = []
        for row in cursor.fetchall():
            meter = dict(row)
            
            # Obtener métricas recientes
            cursor.execute('''
                SELECT 
                    success_rate, total_reads, successful_reads,
                    messages_sent, timestamp
                FROM meter_metrics
                WHERE meter_id = ?
                ORDER BY timestamp DESC
                LIMIT 1
            ''', (meter['id'],))
            
            latest_metric = cursor.fetchone()
            meter['latest_metric'] = dict(latest_metric) if latest_metric else None
            
            meters.append(meter)
        
        conn.close()
        
        return jsonify({
            'success': True,
            'count': len(meters),
            'meters': meters
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo medidores: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/meters/<int:meter_id>', methods=['GET'])
def get_meter_detail(meter_id: int):
    """Obtiene detalles completos de un medidor."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Información básica del medidor
        cursor.execute('SELECT * FROM meters WHERE id = ?', (meter_id,))
        meter_row = cursor.fetchone()
        
        if not meter_row:
            return jsonify({'success': False, 'error': 'Medidor no encontrado'}), 404
        
        meter = dict(meter_row)
        
        # Últimas 10 lecturas
        cursor.execute('''
            SELECT * FROM meter_metrics
            WHERE meter_id = ?
            ORDER BY timestamp DESC
            LIMIT 10
        ''', (meter_id,))
        
        meter['recent_readings'] = [dict(row) for row in cursor.fetchall()]
        
        # Alarmas activas
        cursor.execute('''
            SELECT * FROM alarms
            WHERE meter_id = ? AND status = 'active'
            ORDER BY created_at DESC
        ''', (meter_id,))
        
        meter['active_alarms'] = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        
        return jsonify({
            'success': True,
            'meter': meter
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo detalle del medidor {meter_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/meters/<int:meter_id>/status', methods=['GET'])
def get_meter_status(meter_id: int):
    """Obtiene el estado en tiempo real de un medidor."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Info básica
        cursor.execute('''
            SELECT id, name, ip_address, port, status, last_seen, last_error
            FROM meters WHERE id = ?
        ''', (meter_id,))
        
        meter_row = cursor.fetchone()
        if not meter_row:
            return jsonify({'success': False, 'error': 'Medidor no encontrado'}), 404
        
        meter = dict(meter_row)
        
        # Última lectura
        cursor.execute('''
            SELECT * FROM meter_metrics
            WHERE meter_id = ?
            ORDER BY timestamp DESC
            LIMIT 1
        ''', (meter_id,))
        
        latest = cursor.fetchone()
        meter['latest_metric'] = dict(latest) if latest else None
        
        # Estadísticas de las últimas 24 horas
        yesterday = (datetime.now() - timedelta(days=1)).isoformat()
        cursor.execute('''
            SELECT COUNT(*) as total_readings
            FROM meter_metrics
            WHERE meter_id = ? AND timestamp > ?
        ''', (meter_id, yesterday))
        
        stats = cursor.fetchone()
        meter['stats_24h'] = dict(stats) if stats else {'total_readings': 0}
        
        # Extraer métricas de los logs
        logs = get_meter_logs(meter_id, lines=20)
        
        # Buscar última línea con estadísticas
        success_rate = None
        cycles = None
        mqtt_msgs = None
        
        for log in reversed(logs):
            if 'Cycles=' in log['message'] and 'Success=' in log['message']:
                msg = log['message']
                try:
                    if 'Cycles=' in msg:
                        cycles = int(msg.split('Cycles=')[1].split(',')[0])
                    if 'Success=' in msg:
                        success_rate = float(msg.split('Success=')[1].split('%')[0])
                    if 'MQTT=' in msg:
                        mqtt_msgs = int(msg.split('MQTT=')[1].split(',')[0])
                    break
                except:
                    pass
        
        meter['live_stats'] = {
            'cycles': cycles,
            'success_rate': success_rate,
            'mqtt_messages': mqtt_msgs
        }
        
        conn.close()
        
        return jsonify({
            'success': True,
            'meter_id': meter_id,
            'status': meter
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo estado del medidor {meter_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/meters/<int:meter_id>/logs', methods=['GET'])
def get_meter_logs_endpoint(meter_id: int):
    """Obtiene logs recientes de un medidor específico."""
    lines = request.args.get('lines', 50, type=int)
    
    try:
        logs = get_meter_logs(meter_id, lines=lines)
        
        return jsonify({
            'success': True,
            'meter_id': meter_id,
            'count': len(logs),
            'logs': logs
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo logs del medidor {meter_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/meters/<int:meter_id>/metrics', methods=['GET'])
def get_meter_metrics(meter_id: int):
    """Obtiene métricas históricas de un medidor."""
    limit = request.args.get('limit', 100, type=int)
    since = request.args.get('since', None)
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = '''
            SELECT * FROM meter_metrics
            WHERE meter_id = ?
        '''
        params = [meter_id]
        
        if since:
            query += ' AND timestamp > ?'
            params.append(since)
        
        query += ' ORDER BY timestamp DESC LIMIT ?'
        params.append(limit)
        
        cursor.execute(query, params)
        
        metrics = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        
        return jsonify({
            'success': True,
            'meter_id': meter_id,
            'count': len(metrics),
            'metrics': metrics
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo métricas del medidor {meter_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# ============================================================================
# ENDPOINTS - CONTROL DE MEDIDORES
# ============================================================================

@app.route('/api/meters/<int:meter_id>/pause', methods=['POST'])
def pause_meter(meter_id: int):
    """Pausa el polling de un medidor (cambia status a 'paused')."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE meters 
            SET status = 'paused', updated_at = ?
            WHERE id = ?
        ''', (datetime.now().isoformat(), meter_id))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Medidor {meter_id} pausado")
        
        return jsonify({
            'success': True,
            'message': f'Medidor {meter_id} pausado. Reinicia el servicio para aplicar cambios.',
            'action_required': 'sudo systemctl restart dlms-multi-meter.service'
        })
        
    except Exception as e:
        logger.error(f"Error pausando medidor {meter_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/meters/<int:meter_id>/resume', methods=['POST'])
def resume_meter(meter_id: int):
    """Reanuda el polling de un medidor (cambia status a 'active')."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE meters 
            SET status = 'active', updated_at = ?
            WHERE id = ?
        ''', (datetime.now().isoformat(), meter_id))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Medidor {meter_id} reanudado")
        
        return jsonify({
            'success': True,
            'message': f'Medidor {meter_id} reanudado. Reinicia el servicio para aplicar cambios.',
            'action_required': 'sudo systemctl restart dlms-multi-meter.service'
        })
        
    except Exception as e:
        logger.error(f"Error reanudando medidor {meter_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/meters/<int:meter_id>/test', methods=['POST'])
def test_meter_connection(meter_id: int):
    """Prueba la conexión a un medidor sin afectar el polling."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM meters WHERE id = ?', (meter_id,))
        meter = cursor.fetchone()
        conn.close()
        
        if not meter:
            return jsonify({'success': False, 'error': 'Medidor no encontrado'}), 404
        
        meter = dict(meter)
        
        # Test de ping
        ping_result = subprocess.run(
            ['ping', '-c', '3', '-W', '2', meter['ip_address']],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        ping_success = ping_result.returncode == 0
        
        # Test de puerto TCP
        import socket
        tcp_success = False
        tcp_time = None
        
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5.0)
            start = datetime.now()
            sock.connect((meter['ip_address'], meter['port']))
            tcp_time = (datetime.now() - start).total_seconds()
            tcp_success = True
            sock.close()
        except Exception as e:
            tcp_time = str(e)
        
        return jsonify({
            'success': True,
            'meter_id': meter_id,
            'tests': {
                'ping': {
                    'success': ping_success,
                    'output': ping_result.stdout if ping_success else ping_result.stderr
                },
                'tcp': {
                    'success': tcp_success,
                    'connection_time': tcp_time,
                    'host': meter['ip_address'],
                    'port': meter['port']
                }
            }
        })
        
    except Exception as e:
        logger.error(f"Error probando medidor {meter_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/meters/<int:meter_id>/restart', methods=['POST'])
def restart_meter_worker(meter_id: int):
    """
    Reinicia el worker de un medidor específico.
    Nota: Actualmente requiere reiniciar todo el servicio.
    """
    try:
        # Por ahora, reiniciamos todo el servicio
        # En el futuro podríamos implementar señales para workers individuales
        
        result = subprocess.run(
            ['sudo', 'systemctl', 'restart', SERVICE_NAME],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        success = result.returncode == 0
        
        return jsonify({
            'success': success,
            'message': f'Servicio reiniciado (afecta a todos los medidores)',
            'note': 'El worker del medidor {meter_id} se reiniciará con todo el servicio'
        })
        
    except Exception as e:
        logger.error(f"Error reiniciando worker del medidor {meter_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# ============================================================================
# ENDPOINTS - SISTEMA
# ============================================================================

@app.route('/api/system/health', methods=['GET'])
def get_system_health():
    """Obtiene el estado general del sistema."""
    try:
        service_status = get_service_status()
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Contar medidores por estado
        cursor.execute('''
            SELECT status, COUNT(*) as count
            FROM meters
            GROUP BY status
        ''')
        
        meter_counts = {row['status']: row['count'] for row in cursor.fetchall()}
        
        # Total de lecturas en las últimas 24h
        yesterday = (datetime.now() - timedelta(days=1)).isoformat()
        cursor.execute('''
            SELECT COUNT(*) as total
            FROM meter_metrics
            WHERE timestamp > ?
        ''', (yesterday,))
        
        readings_24h = cursor.fetchone()['total']
        
        # Alarmas activas
        cursor.execute('''
            SELECT severity, COUNT(*) as count
            FROM alarms
            WHERE status = 'active'
            GROUP BY severity
        ''')
        
        active_alarms = {row['severity']: row['count'] for row in cursor.fetchall()}
        
        conn.close()
        
        return jsonify({
            'success': True,
            'timestamp': datetime.now().isoformat(),
            'service': service_status,
            'meters': {
                'total': sum(meter_counts.values()),
                'by_status': meter_counts
            },
            'readings_24h': readings_24h,
            'active_alarms': active_alarms
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo salud del sistema: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/system/logs', methods=['GET'])
def get_system_logs():
    """Obtiene logs generales del sistema."""
    lines = request.args.get('lines', 100, type=int)
    since = request.args.get('since', None)
    
    try:
        logs = get_journalctl_logs(SERVICE_NAME, lines=lines, since=since)
        
        return jsonify({
            'success': True,
            'count': len(logs),
            'logs': logs
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo logs del sistema: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/system/service/restart', methods=['POST'])
def restart_service():
    """Reinicia el servicio completo."""
    try:
        result = subprocess.run(
            ['sudo', 'systemctl', 'restart', SERVICE_NAME],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        success = result.returncode == 0
        
        return jsonify({
            'success': success,
            'message': 'Servicio reiniciado' if success else 'Error reiniciando servicio',
            'output': result.stdout if success else result.stderr
        })
        
    except Exception as e:
        logger.error(f"Error reiniciando servicio: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# ============================================================================
# ENDPOINT RAÍZ
# ============================================================================

@app.route('/')
def index():
    """Página de inicio con documentación de la API."""
    return '''
    <html>
    <head><title>DLMS Meter Control API</title></head>
    <body style="font-family: monospace; padding: 20px;">
        <h1>🔌 DLMS Meter Control API</h1>
        <p>API REST para control y monitoreo de medidores DLMS</p>
        
        <h2>📊 Información</h2>
        <ul>
            <li><a href="/api/meters">GET /api/meters</a> - Lista todos los medidores</li>
            <li>GET /api/meters/&lt;id&gt; - Detalles de un medidor</li>
            <li>GET /api/meters/&lt;id&gt;/status - Estado en tiempo real</li>
            <li>GET /api/meters/&lt;id&gt;/logs - Logs del medidor</li>
            <li>GET /api/meters/&lt;id&gt;/metrics - Métricas históricas</li>
        </ul>
        
        <h2>⚙️ Control</h2>
        <ul>
            <li>POST /api/meters/&lt;id&gt;/pause - Pausar medidor</li>
            <li>POST /api/meters/&lt;id&gt;/resume - Reanudar medidor</li>
            <li>POST /api/meters/&lt;id&gt;/test - Probar conexión</li>
            <li>POST /api/meters/&lt;id&gt;/restart - Reiniciar worker</li>
        </ul>
        
        <h2>🖥️ Sistema</h2>
        <ul>
            <li><a href="/api/system/health">GET /api/system/health</a> - Estado del sistema</li>
            <li>GET /api/system/logs - Logs del sistema</li>
            <li>POST /api/system/service/restart - Reiniciar servicio</li>
        </ul>
        
        <h2>💡 Ejemplos</h2>
        <pre>
# Ver todos los medidores
curl http://localhost:5001/api/meters

# Ver estado del medidor 1
curl http://localhost:5001/api/meters/1/status

# Pausar medidor 2
curl -X POST http://localhost:5001/api/meters/2/pause

# Ver logs del medidor 1 (últimas 20 líneas)
curl http://localhost:5001/api/meters/1/logs?lines=20

# Probar conexión al medidor 2
curl -X POST http://localhost:5001/api/meters/2/test
        </pre>
    </body>
    </html>
    '''

# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='DLMS Meter Control API')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, default=5001, help='Port to bind to')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    
    args = parser.parse_args()
    
    logger.info(f"🚀 Iniciando Meter Control API en {args.host}:{args.port}")
    logger.info(f"📖 Documentación disponible en http://{args.host}:{args.port}/")
    
    app.run(host=args.host, port=args.port, debug=args.debug)
