#!/usr/bin/env python3
"""
Sistema de Monitoreo de Salud y QoS
Detecta problemas, genera diagnósticos y recomienda acciones
"""

import re
import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple
from collections import defaultdict, Counter
import subprocess


class SystemHealthMonitor:
    """Monitor de salud del sistema DLMS"""
    
    def __init__(self, db_path: str = "data/admin.db"):
        self.db_path = db_path
        self.error_patterns = {
            'socket_closed': re.compile(r'Socket closed while waiting for frame'),
            'hdlc_boundary': re.compile(r'Invalid HDLC frame boundary'),
            'hdlc_checksum': re.compile(r'Checksum mismatch'),
            'hdlc_unterminated': re.compile(r'unterminated HDLC address'),
            'connection_timeout': re.compile(r'Connection.*timed out|timeout'),
            'connection_refused': re.compile(r'Connection refused'),
            'network_unreachable': re.compile(r'Network.*unreachable'),
            'mqtt_disconnect': re.compile(r'MQTT.*disconnect|broker.*disconnect'),
            'read_failure': re.compile(r'Failed to read value|Reading failed'),
        }
        
    def get_service_logs(self, minutes: int = 60) -> List[str]:
        """Obtener logs del servicio"""
        try:
            cmd = f"sudo journalctl -u dlms-multi-meter.service --since '{minutes} minutes ago' --no-pager"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            return result.stdout.split('\n')
        except Exception as e:
            print(f"Error obteniendo logs: {e}")
            return []
    
    def analyze_error_patterns(self, logs: List[str]) -> Dict[str, int]:
        """Analizar patrones de error en logs"""
        error_counts = defaultdict(int)
        
        for log in logs:
            for error_name, pattern in self.error_patterns.items():
                if pattern.search(log):
                    error_counts[error_name] += 1
        
        return dict(error_counts)
    
    def get_meter_metrics(self) -> List[Dict]:
        """Obtener métricas de medidores desde BD"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT 
                    id, name, ip_address, port, status
                FROM meters
            ''')
            
            meters = []
            for row in cursor.fetchall():
                meters.append({
                    'id': row[0],
                    'name': row[1],
                    'ip': row[2],
                    'port': row[3],
                    'status': row[4],
                    'error_count': 0
                })
            
            conn.close()
            return meters
            
        except Exception as e:
            print(f"Error obteniendo métricas: {e}")
            return []
    
    def extract_meter_stats_from_logs(self, logs: List[str]) -> Dict[int, Dict]:
        """Extraer estadísticas de medidores desde logs"""
        stats = {}
        
        # Pattern: Meter X (name): Cycles=Y, Success=Z%, MQTT=W, Runtime=Rs
        pattern = re.compile(
            r'Meter (\d+) \(([^)]+)\): Cycles=(\d+), Success=([\d.]+)%, MQTT=(\d+), Runtime=(\d+)s'
        )
        
        for log in logs:
            match = pattern.search(log)
            if match:
                meter_id = int(match.group(1))
                stats[meter_id] = {
                    'name': match.group(2),
                    'cycles': int(match.group(3)),
                    'success_rate': float(match.group(4)),
                    'mqtt_messages': int(match.group(5)),
                    'runtime': int(match.group(6))
                }
        
        return stats
    
    def diagnose_meter_issues(self, meter_id: int, logs: List[str]) -> List[str]:
        """Diagnosticar problemas de un medidor específico"""
        issues = []
        meter_logs = [log for log in logs if f'Meter[{meter_id}' in log or f'Meter {meter_id}' in log]
        
        # Analizar errores específicos
        error_counts = self.analyze_error_patterns(meter_logs)
        
        # Socket closed - problema de conexión TCP/red
        if error_counts.get('socket_closed', 0) > 3:
            issues.append({
                'severity': 'HIGH',
                'category': 'NETWORK',
                'issue': f"Socket cerrado repetidamente ({error_counts['socket_closed']} veces)",
                'probable_causes': [
                    'Medidor físico apagado o desconectado',
                    'Firewall bloqueando conexiones',
                    'Problema de red intermitente',
                    'Puerto DLMS (3333) inaccesible'
                ],
                'actions': [
                    'Verificar alimentación del medidor',
                    'Ping al medidor para verificar conectividad',
                    'Verificar puerto 3333 con netcat',
                    'Revisar configuración de firewall'
                ]
            })
        
        # HDLC errors - problema de protocolo
        hdlc_errors = (error_counts.get('hdlc_boundary', 0) + 
                      error_counts.get('hdlc_checksum', 0) +
                      error_counts.get('hdlc_unterminated', 0))
        
        if hdlc_errors > 5:
            issues.append({
                'severity': 'HIGH',
                'category': 'PROTOCOL',
                'issue': f"Múltiples errores HDLC ({hdlc_errors} total)",
                'probable_causes': [
                    'Interferencia electromagnética en comunicación',
                    'Baudrate incorrecto',
                    'Cable de comunicación defectuoso',
                    'Medidor con firmware corrupto',
                    'Conflicto con otra conexión simultánea'
                ],
                'actions': [
                    'Verificar cableado de comunicación',
                    'Revisar configuración DLMS (baudrate, timeout)',
                    'Asegurar que solo un cliente conecta al medidor',
                    'Incrementar timeout de conexión',
                    'Verificar compatibilidad de protocolo'
                ]
            })
        
        # Read failures - problema de lectura
        if error_counts.get('read_failure', 0) > 10:
            issues.append({
                'severity': 'MEDIUM',
                'category': 'DATA',
                'issue': f"Múltiples fallos de lectura ({error_counts['read_failure']} veces)",
                'probable_causes': [
                    'OBIS codes incorrectos para este medidor',
                    'Registros no soportados por el medidor',
                    'Permisos de lectura insuficientes',
                    'Timeout muy corto para respuesta del medidor'
                ],
                'actions': [
                    'Verificar OBIS codes configurados',
                    'Incrementar timeout de lectura',
                    'Revisar permisos/password DLMS',
                    'Probar lectura individual de cada registro'
                ]
            })
        
        # MQTT disconnects - problema de publicación
        if error_counts.get('mqtt_disconnect', 0) > 2:
            issues.append({
                'severity': 'MEDIUM',
                'category': 'MQTT',
                'issue': f"Desconexiones MQTT frecuentes ({error_counts['mqtt_disconnect']} veces)",
                'probable_causes': [
                    'Broker MQTT inestable',
                    'Red local con problemas',
                    'Demasiados mensajes (throttling)',
                    'Problemas de memoria en el cliente'
                ],
                'actions': [
                    'Verificar estado del broker Mosquitto',
                    'Revisar logs de Mosquitto',
                    'Ajustar QoS y keep-alive',
                    'Verificar uso de memoria del servicio'
                ]
            })
        
        # No issues found
        if not issues:
            # Check if meter has 0% success rate
            stats_pattern = re.compile(f'Meter {meter_id}.*Success=0\\.0%')
            if any(stats_pattern.search(log) for log in meter_logs):
                issues.append({
                    'severity': 'CRITICAL',
                    'category': 'CONNECTION',
                    'issue': 'Medidor sin conexión exitosa (0% success rate)',
                    'probable_causes': [
                        'Medidor nunca se conectó desde el inicio',
                        'IP o puerto incorrectos',
                        'Credenciales DLMS incorrectas',
                        'Medidor en modo de bajo consumo/sleep'
                    ],
                    'actions': [
                        'Verificar IP y puerto en configuración',
                        'Verificar credenciales DLMS (client_sap, server)',
                        'Probar conexión manual con dlms_reader.py',
                        'Verificar que medidor esté en modo operacional'
                    ]
                })
        
        return issues
    
    def generate_health_report(self, minutes: int = 60) -> Dict:
        """Generar reporte completo de salud del sistema"""
        print(f"🔍 Analizando logs de los últimos {minutes} minutos...\n")
        
        logs = self.get_service_logs(minutes)
        meters = self.get_meter_metrics()
        stats = self.extract_meter_stats_from_logs(logs)
        error_summary = self.analyze_error_patterns(logs)
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'analysis_period_minutes': minutes,
            'overall_health': 'UNKNOWN',
            'meters': {},
            'system_errors': error_summary,
            'recommendations': []
        }
        
        # Analizar cada medidor
        critical_issues = 0
        high_issues = 0
        
        for meter in meters:
            meter_id = meter['id']
            meter_stats = stats.get(meter_id, {})
            
            # Diagnosticar problemas
            issues = self.diagnose_meter_issues(meter_id, logs)
            
            # Contar severidad
            for issue in issues:
                if issue['severity'] == 'CRITICAL':
                    critical_issues += 1
                elif issue['severity'] == 'HIGH':
                    high_issues += 1
            
            # Health status del medidor
            success_rate = meter_stats.get('success_rate', 0)
            if success_rate >= 90:
                health = 'HEALTHY'
            elif success_rate >= 50:
                health = 'DEGRADED'
            elif success_rate > 0:
                health = 'CRITICAL'
            else:
                health = 'DOWN'
            
            report['meters'][meter_id] = {
                'name': meter['name'],
                'ip': meter['ip'],
                'port': meter['port'],
                'status': meter['status'],
                'health': health,
                'stats': meter_stats,
                'issues': issues
            }
        
        # Determinar salud general
        if critical_issues > 0:
            report['overall_health'] = 'CRITICAL'
        elif high_issues > 1:
            report['overall_health'] = 'DEGRADED'
        elif any(m['health'] == 'HEALTHY' for m in report['meters'].values()):
            report['overall_health'] = 'HEALTHY'
        else:
            report['overall_health'] = 'WARNING'
        
        # Recomendaciones generales
        if error_summary.get('socket_closed', 0) > 5:
            report['recommendations'].append({
                'priority': 'HIGH',
                'action': 'Verificar conectividad de red a medidores',
                'reason': 'Múltiples errores de socket cerrado detectados'
            })
        
        if error_summary.get('hdlc_boundary', 0) > 10:
            report['recommendations'].append({
                'priority': 'HIGH',
                'action': 'Revisar configuración DLMS y calidad de comunicación',
                'reason': 'Errores HDLC frecuentes indican problemas de protocolo'
            })
        
        return report
    
    def print_report(self, report: Dict):
        """Imprimir reporte formateado"""
        health_icons = {
            'HEALTHY': '✅',
            'DEGRADED': '⚠️',
            'CRITICAL': '🔴',
            'DOWN': '❌',
            'WARNING': '⚠️',
            'UNKNOWN': '❓'
        }
        
        severity_icons = {
            'CRITICAL': '🔴',
            'HIGH': '🟠',
            'MEDIUM': '🟡',
            'LOW': '🟢'
        }
        
        print("="*80)
        print(f"  REPORTE DE SALUD DEL SISTEMA DLMS")
        print("="*80)
        print(f"Timestamp: {report['timestamp']}")
        print(f"Período analizado: {report['analysis_period_minutes']} minutos")
        print(f"Salud general: {health_icons.get(report['overall_health'])} {report['overall_health']}")
        print()
        
        # Resumen de errores del sistema
        if report['system_errors']:
            print("📊 RESUMEN DE ERRORES DEL SISTEMA:")
            for error_type, count in sorted(report['system_errors'].items(), key=lambda x: -x[1]):
                print(f"   • {error_type.replace('_', ' ').title()}: {count}")
            print()
        
        # Información por medidor
        print("🏭 ESTADO DE MEDIDORES:")
        print()
        
        for meter_id, meter_info in report['meters'].items():
            print(f"┌─ MEDIDOR {meter_id}: {meter_info['name']}")
            print(f"│  {health_icons.get(meter_info['health'])} Estado: {meter_info['health']}")
            print(f"│  📍 {meter_info['ip']}:{meter_info['port']}")
            
            if meter_info['stats']:
                stats = meter_info['stats']
                print(f"│  📈 Ciclos: {stats.get('cycles', 0)}")
                print(f"│  ✓  Success Rate: {stats.get('success_rate', 0):.1f}%")
                print(f"│  📤 Mensajes MQTT: {stats.get('mqtt_messages', 0)}")
                print(f"│  ⏱️  Runtime: {stats.get('runtime', 0)}s")
            else:
                print(f"│  ℹ️  Sin estadísticas disponibles en período analizado")
            
            # Problemas detectados
            if meter_info['issues']:
                print(f"│")
                print(f"│  🔍 PROBLEMAS DETECTADOS:")
                for i, issue in enumerate(meter_info['issues'], 1):
                    print(f"│")
                    print(f"│  {severity_icons.get(issue['severity'])} Problema #{i} [{issue['severity']}] - {issue['category']}")
                    print(f"│     {issue['issue']}")
                    print(f"│")
                    print(f"│     Causas probables:")
                    for cause in issue['probable_causes']:
                        print(f"│       • {cause}")
                    print(f"│")
                    print(f"│     Acciones recomendadas:")
                    for action in issue['actions']:
                        print(f"│       → {action}")
            else:
                print(f"│  ✅ Sin problemas detectados")
            
            print(f"└{'─'*78}")
            print()
        
        # Recomendaciones generales
        if report['recommendations']:
            print("💡 RECOMENDACIONES GENERALES:")
            for rec in report['recommendations']:
                priority_icon = severity_icons.get(rec['priority'], '•')
                print(f"{priority_icon} [{rec['priority']}] {rec['action']}")
                print(f"   Razón: {rec['reason']}")
            print()
        
        print("="*80)
    
    def save_report(self, report: Dict, filename: str = None):
        """Guardar reporte en archivo JSON"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"health_report_{timestamp}.json"
        
        output_dir = Path("logs/health_reports")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        filepath = output_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Reporte guardado en: {filepath}")
        return filepath


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Sistema de Monitoreo de Salud DLMS')
    parser.add_argument('--minutes', '-m', type=int, default=60,
                       help='Minutos de logs a analizar (default: 60)')
    parser.add_argument('--save', '-s', action='store_true',
                       help='Guardar reporte en archivo JSON')
    parser.add_argument('--db', default='data/admin.db',
                       help='Ruta a la base de datos (default: data/admin.db)')
    
    args = parser.parse_args()
    
    monitor = SystemHealthMonitor(db_path=args.db)
    report = monitor.generate_health_report(minutes=args.minutes)
    monitor.print_report(report)
    
    if args.save:
        monitor.save_report(report)
    
    # Exit code based on health
    exit_codes = {
        'HEALTHY': 0,
        'WARNING': 0,
        'DEGRADED': 1,
        'CRITICAL': 2,
        'UNKNOWN': 3
    }
    
    exit(exit_codes.get(report['overall_health'], 3))


if __name__ == '__main__':
    main()
