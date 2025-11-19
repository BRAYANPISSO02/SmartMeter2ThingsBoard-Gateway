#!/usr/bin/env python3
"""
Cliente CLI para controlar medidores DLMS via API

Comandos:
  list              - Lista todos los medidores
  status <id>       - Estado de un medidor
  logs <id>         - Logs de un medidor
  follow <id>       - Seguir logs en tiempo real
  pause <id>        - Pausar medidor
  resume <id>       - Reanudar medidor
  test <id>         - Probar conexión
  restart <id>      - Reiniciar worker
  health            - Estado del sistema

Ejemplos:
  python3 meter_cli.py list
  python3 meter_cli.py status 1
  python3 meter_cli.py follow 2
  python3 meter_cli.py pause 2
"""

import requests
import argparse
import json
import time
import sys
from datetime import datetime
from typing import Optional

# Configuración
API_BASE_URL = 'http://localhost:5001/api'

# Colores ANSI
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def colored(text: str, color: str) -> str:
    """Retorna texto coloreado."""
    return f"{color}{text}{Colors.ENDC}"

def print_header(text: str):
    """Imprime un encabezado."""
    print()
    print(colored("=" * 80, Colors.BOLD))
    print(colored(text, Colors.HEADER + Colors.BOLD))
    print(colored("=" * 80, Colors.BOLD))
    print()

def print_error(text: str):
    """Imprime un mensaje de error."""
    print(colored(f"❌ ERROR: {text}", Colors.RED))

def print_success(text: str):
    """Imprime un mensaje de éxito."""
    print(colored(f"✅ {text}", Colors.GREEN))

def print_warning(text: str):
    """Imprime una advertencia."""
    print(colored(f"⚠️  {text}", Colors.YELLOW))

def print_info(text: str):
    """Imprime información."""
    print(colored(f"ℹ️  {text}", Colors.CYAN))

def api_request(endpoint: str, method: str = 'GET', data: dict = None) -> Optional[dict]:
    """Hace una petición a la API."""
    url = f"{API_BASE_URL}{endpoint}"
    
    try:
        if method == 'GET':
            response = requests.get(url, timeout=10)
        elif method == 'POST':
            response = requests.post(url, json=data, timeout=10)
        else:
            print_error(f"Método HTTP no soportado: {method}")
            return None
        
        response.raise_for_status()
        return response.json()
    
    except requests.exceptions.ConnectionError:
        print_error("No se pudo conectar a la API. ¿Está corriendo el servidor?")
        print_info("Inicia el servidor con: python3 meter_control_api.py")
        return None
    except requests.exceptions.Timeout:
        print_error("Timeout en la petición a la API")
        return None
    except requests.exceptions.HTTPError as e:
        print_error(f"Error HTTP: {e}")
        return None
    except Exception as e:
        print_error(f"Error inesperado: {e}")
        return None

# ============================================================================
# COMANDOS
# ============================================================================

def cmd_list(args):
    """Lista todos los medidores."""
    print_header("📋 LISTA DE MEDIDORES")
    
    result = api_request('/meters')
    if not result or not result.get('success'):
        return
    
    meters = result.get('meters', [])
    
    if not meters:
        print_warning("No hay medidores configurados")
        return
    
    # Tabla
    print(f"{'ID':<5} {'Nombre':<25} {'IP':<17} {'Puerto':<7} {'Estado':<10} {'Última Lectura'}")
    print("-" * 100)
    
    for meter in meters:
        meter_id = meter['id']
        name = meter['name'][:24]
        ip = meter['ip_address']
        port = meter['port']
        status = meter['status']
        
        # Color según estado
        if status == 'active':
            status_colored = colored(status, Colors.GREEN)
        elif status == 'paused':
            status_colored = colored(status, Colors.YELLOW)
        else:
            status_colored = colored(status, Colors.RED)
        
        # Última lectura/métrica
        latest = meter.get('latest_metric')
        if latest:
            success_rate = latest.get('success_rate', 'N/A')
            last_reading = f"{success_rate}% éxito"
        else:
            last_reading = colored("Sin datos", Colors.RED)
        
        print(f"{meter_id:<5} {name:<25} {ip:<17} {port:<7} {status_colored:<20} {last_reading}")
    
    print()
    print_info(f"Total: {len(meters)} medidores")

def cmd_status(args):
    """Muestra el estado detallado de un medidor."""
    meter_id = args.meter_id
    
    print_header(f"📊 ESTADO DEL MEDIDOR {meter_id}")
    
    result = api_request(f'/meters/{meter_id}/status')
    if not result or not result.get('success'):
        return
    
    status = result['status']
    
    # Información básica
    print(colored("Información Básica:", Colors.BOLD))
    print(f"  ID:         {status['id']}")
    print(f"  Nombre:     {status['name']}")
    print(f"  IP:         {status['ip_address']}:{status['port']}")
    print(f"  Estado:     {colored(status['status'], Colors.GREEN if status['status'] == 'active' else Colors.YELLOW)}")
    print(f"  Última vez: {status.get('last_seen', 'N/A')}")
    
    # Estadísticas en vivo
    live = status.get('live_stats', {})
    if live.get('cycles') is not None:
        print()
        print(colored("Estadísticas en Vivo:", Colors.BOLD))
        print(f"  Ciclos:         {live['cycles']}")
        success_rate_str = f"{live['success_rate']}%"
        success_color = Colors.GREEN if live['success_rate'] > 90 else Colors.YELLOW
        print(f"  Tasa de éxito:  {colored(success_rate_str, success_color)}")
        print(f"  Mensajes MQTT:  {live['mqtt_messages']}")
    
    # Última lectura/métrica
    latest = status.get('latest_metric')
    if latest:
        print()
        print(colored("Última Métrica:", Colors.BOLD))
        print(f"  Timestamp:      {latest['timestamp']}")
        print(f"  Lecturas:       {latest.get('successful_reads', 0)}/{latest.get('total_reads', 0)}")
        print(f"  Tasa de éxito:  {latest.get('success_rate', 0):.1f}%")
        print(f"  Mensajes MQTT:  {latest.get('messages_sent', 0)}")
        if latest.get('cache_hit_rate'):
            print(f"  Cache hit rate: {latest.get('cache_hit_rate', 0):.1f}%")
    else:
        print()
        print_warning("Sin métricas disponibles")
    
    # Estadísticas 24h
    stats = status.get('stats_24h', {})
    if stats.get('total_readings', 0) > 0:
        print()
        print(colored("Últimas 24 horas:", Colors.BOLD))
        print(f"  Total lecturas: {stats['total_readings']}")

def cmd_logs(args):
    """Muestra los logs de un medidor."""
    meter_id = args.meter_id
    lines = args.lines
    
    print_header(f"📝 LOGS DEL MEDIDOR {meter_id}")
    
    result = api_request(f'/meters/{meter_id}/logs?lines={lines}')
    if not result or not result.get('success'):
        return
    
    logs = result.get('logs', [])
    
    if not logs:
        print_warning("No hay logs disponibles")
        return
    
    # Imprimir logs con colores según nivel
    for log in logs:
        timestamp = log.get('timestamp', '')
        level = log.get('level', 'INFO')
        message = log.get('message', '')
        
        # Color según nivel
        if 'ERROR' in level:
            level_colored = colored(level, Colors.RED)
        elif 'WARNING' in level:
            level_colored = colored(level, Colors.YELLOW)
        elif 'SUCCESS' in level or '✅' in message:
            level_colored = colored(level, Colors.GREEN)
        else:
            level_colored = level
        
        print(f"{timestamp} [{level_colored}] {message}")
    
    print()
    print_info(f"Mostrando {len(logs)} líneas")

def cmd_follow(args):
    """Sigue los logs de un medidor en tiempo real."""
    meter_id = args.meter_id
    
    print_header(f"👁️  SIGUIENDO MEDIDOR {meter_id}")
    print_info("Presiona Ctrl+C para detener")
    print()
    
    last_log_count = 0
    
    try:
        while True:
            result = api_request(f'/meters/{meter_id}/logs?lines=10')
            if result and result.get('success'):
                logs = result.get('logs', [])
                
                # Mostrar solo logs nuevos
                if len(logs) > last_log_count:
                    new_logs = logs[last_log_count:]
                    for log in new_logs:
                        timestamp = log.get('timestamp', '')
                        message = log.get('message', '')
                        
                        # Color según contenido
                        if '❌' in message or 'ERROR' in message:
                            print(colored(f"{timestamp} {message}", Colors.RED))
                        elif '✅' in message or 'Successfully' in message:
                            print(colored(f"{timestamp} {message}", Colors.GREEN))
                        elif '⚠️' in message or 'WARNING' in message:
                            print(colored(f"{timestamp} {message}", Colors.YELLOW))
                        else:
                            print(f"{timestamp} {message}")
                    
                    last_log_count = len(logs)
            
            time.sleep(2)  # Actualizar cada 2 segundos
    
    except KeyboardInterrupt:
        print()
        print_info("Detenido por el usuario")

def cmd_pause(args):
    """Pausa un medidor."""
    meter_id = args.meter_id
    
    print_header(f"⏸️  PAUSANDO MEDIDOR {meter_id}")
    
    result = api_request(f'/meters/{meter_id}/pause', method='POST')
    if not result:
        return
    
    if result.get('success'):
        print_success(result.get('message', 'Medidor pausado'))
        if result.get('action_required'):
            print_warning(f"Acción requerida: {result['action_required']}")
    else:
        print_error(result.get('error', 'Error desconocido'))

def cmd_resume(args):
    """Reanuda un medidor."""
    meter_id = args.meter_id
    
    print_header(f"▶️  REANUDANDO MEDIDOR {meter_id}")
    
    result = api_request(f'/meters/{meter_id}/resume', method='POST')
    if not result:
        return
    
    if result.get('success'):
        print_success(result.get('message', 'Medidor reanudado'))
        if result.get('action_required'):
            print_warning(f"Acción requerida: {result['action_required']}")
    else:
        print_error(result.get('error', 'Error desconocido'))

def cmd_test(args):
    """Prueba la conexión a un medidor."""
    meter_id = args.meter_id
    
    print_header(f"🔍 PROBANDO MEDIDOR {meter_id}")
    
    result = api_request(f'/meters/{meter_id}/test', method='POST')
    if not result or not result.get('success'):
        return
    
    tests = result.get('tests', {})
    
    # Test de ping
    ping = tests.get('ping', {})
    print(colored("Test de Ping:", Colors.BOLD))
    if ping.get('success'):
        print_success("Ping exitoso")
        print(ping.get('output', ''))
    else:
        print_error("Ping falló")
        print(ping.get('output', ''))
    
    # Test de TCP
    tcp = tests.get('tcp', {})
    print()
    print(colored("Test de Puerto TCP:", Colors.BOLD))
    print(f"  Host: {tcp.get('host')}")
    print(f"  Port: {tcp.get('port')}")
    
    if tcp.get('success'):
        print_success(f"Conexión exitosa ({tcp.get('connection_time')*1000:.1f}ms)")
    else:
        print_error(f"Conexión falló: {tcp.get('connection_time')}")

def cmd_restart(args):
    """Reinicia el worker de un medidor."""
    meter_id = args.meter_id
    
    print_header(f"🔄 REINICIANDO MEDIDOR {meter_id}")
    
    result = api_request(f'/meters/{meter_id}/restart', method='POST')
    if not result:
        return
    
    if result.get('success'):
        print_success(result.get('message', 'Worker reiniciado'))
        if result.get('note'):
            print_info(result['note'])
    else:
        print_error(result.get('error', 'Error desconocido'))

def cmd_health(args):
    """Muestra el estado general del sistema."""
    print_header("🏥 SALUD DEL SISTEMA")
    
    result = api_request('/system/health')
    if not result or not result.get('success'):
        return
    
    # Estado del servicio
    service = result.get('service', {})
    print(colored("Servicio:", Colors.BOLD))
    status = service.get('status', 'unknown')
    if status == 'running':
        print(f"  Estado: {colored('🟢 Activo', Colors.GREEN)}")
    else:
        print(f"  Estado: {colored('🔴 Detenido', Colors.RED)}")
    
    if service.get('since'):
        print(f"  Desde:  {service['since']}")
    
    # Medidores
    meters = result.get('meters', {})
    print()
    print(colored("Medidores:", Colors.BOLD))
    print(f"  Total: {meters.get('total', 0)}")
    
    by_status = meters.get('by_status', {})
    for status, count in by_status.items():
        if status == 'active':
            print(f"    {colored('✅ Activos:', Colors.GREEN)} {count}")
        elif status == 'paused':
            print(f"    {colored('⏸️  Pausados:', Colors.YELLOW)} {count}")
        else:
            print(f"    {colored(f'❌ {status}:', Colors.RED)} {count}")
    
    # Lecturas
    readings = result.get('readings_24h', 0)
    print()
    print(colored("Actividad (24h):", Colors.BOLD))
    print(f"  Lecturas: {readings}")
    
    # Alarmas
    alarms = result.get('active_alarms', {})
    if alarms:
        print()
        print(colored("Alarmas Activas:", Colors.BOLD))
        for severity, count in alarms.items():
            color = Colors.RED if severity == 'critical' else Colors.YELLOW
            print(f"  {colored(severity.capitalize(), color)}: {count}")

# ============================================================================
# MAIN
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description='Cliente CLI para controlar medidores DLMS',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Comando a ejecutar')
    
    # list
    subparsers.add_parser('list', help='Lista todos los medidores')
    
    # status
    parser_status = subparsers.add_parser('status', help='Estado de un medidor')
    parser_status.add_argument('meter_id', type=int, help='ID del medidor')
    
    # logs
    parser_logs = subparsers.add_parser('logs', help='Logs de un medidor')
    parser_logs.add_argument('meter_id', type=int, help='ID del medidor')
    parser_logs.add_argument('--lines', type=int, default=50, help='Número de líneas')
    
    # follow
    parser_follow = subparsers.add_parser('follow', help='Seguir logs en tiempo real')
    parser_follow.add_argument('meter_id', type=int, help='ID del medidor')
    
    # pause
    parser_pause = subparsers.add_parser('pause', help='Pausar medidor')
    parser_pause.add_argument('meter_id', type=int, help='ID del medidor')
    
    # resume
    parser_resume = subparsers.add_parser('resume', help='Reanudar medidor')
    parser_resume.add_argument('meter_id', type=int, help='ID del medidor')
    
    # test
    parser_test = subparsers.add_parser('test', help='Probar conexión')
    parser_test.add_argument('meter_id', type=int, help='ID del medidor')
    
    # restart
    parser_restart = subparsers.add_parser('restart', help='Reiniciar worker')
    parser_restart.add_argument('meter_id', type=int, help='ID del medidor')
    
    # health
    subparsers.add_parser('health', help='Estado del sistema')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Ejecutar comando
    commands = {
        'list': cmd_list,
        'status': cmd_status,
        'logs': cmd_logs,
        'follow': cmd_follow,
        'pause': cmd_pause,
        'resume': cmd_resume,
        'test': cmd_test,
        'restart': cmd_restart,
        'health': cmd_health
    }
    
    cmd_func = commands.get(args.command)
    if cmd_func:
        cmd_func(args)
    else:
        print_error(f"Comando desconocido: {args.command}")

if __name__ == '__main__':
    main()
