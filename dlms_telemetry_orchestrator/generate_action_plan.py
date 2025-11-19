#!/usr/bin/env python3
"""
Generador de Action Plan
Analiza diagnóstico y crea plan de acción priorizado
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List


class ActionPlanGenerator:
    """Genera planes de acción basados en diagnóstico"""
    
    def __init__(self):
        self.priority_scores = {
            'CRITICAL': 100,
            'HIGH': 75,
            'MEDIUM': 50,
            'LOW': 25
        }
    
    def load_latest_report(self) -> Dict:
        """Cargar último reporte de salud"""
        reports_dir = Path("logs/health_reports")
        
        if not reports_dir.exists():
            print("❌ No se encontraron reportes de salud")
            sys.exit(1)
        
        reports = sorted(reports_dir.glob("health_report_*.json"), reverse=True)
        
        if not reports:
            print("❌ No hay reportes disponibles")
            sys.exit(1)
        
        latest = reports[0]
        print(f"📄 Cargando reporte: {latest.name}\n")
        
        with open(latest, 'r') as f:
            return json.load(f)
    
    def generate_action_plan(self, report: Dict) -> Dict:
        """Generar plan de acción desde reporte"""
        
        plan = {
            'generated_at': datetime.now().isoformat(),
            'based_on_report': report['timestamp'],
            'system_health': report['overall_health'],
            'immediate_actions': [],
            'short_term_actions': [],
            'long_term_actions': [],
            'preventive_measures': []
        }
        
        # Analizar cada medidor
        for meter_id, meter_info in report.get('meters', {}).items():
            meter_name = meter_info['name']
            
            # Medidor DOWN - CRÍTICO
            if meter_info['health'] == 'DOWN':
                plan['immediate_actions'].append({
                    'priority': 'CRITICAL',
                    'target': f"Medidor {meter_id} ({meter_name})",
                    'action': 'Restablecer conexión del medidor',
                    'steps': [
                        f"1. Verificar que medidor en {meter_info['ip']}:{meter_info['port']} esté encendido",
                        f"2. Probar conectividad: ping {meter_info['ip']}",
                        f"3. Verificar puerto DLMS: nc -zv {meter_info['ip']} {meter_info['port']}",
                        "4. Revisar credenciales DLMS en base de datos",
                        "5. Intentar conexión manual: python3 -c \"from dlms_reader import DLMSClient; client = DLMSClient(...)\"",
                    ],
                    'estimated_time': '15-30 minutos',
                    'impact': 'Sin este medidor no hay telemetría para este dispositivo'
                })
            
            # Medidor CRITICAL - success rate muy bajo
            elif meter_info['health'] == 'CRITICAL':
                success_rate = meter_info['stats'].get('success_rate', 0)
                plan['immediate_actions'].append({
                    'priority': 'HIGH',
                    'target': f"Medidor {meter_id} ({meter_name})",
                    'action': f'Mejorar tasa de éxito ({success_rate:.1f}% actual)',
                    'steps': [
                        "1. Revisar logs detallados del medidor",
                        "2. Identificar tipo de error más frecuente (HDLC, socket, timeout)",
                        "3. Si HDLC errors: verificar cableado y configuración baudrate",
                        "4. Si socket errors: verificar firewall y conectividad de red",
                        "5. Incrementar timeouts si hay muchos timeout errors",
                        "6. Considerar limitar polling rate (aumentar intervalo)"
                    ],
                    'estimated_time': '30-60 minutos',
                    'impact': f'Pérdida de ~{100-success_rate:.0f}% de lecturas'
                })
            
            # Procesar issues específicos
            for issue in meter_info.get('issues', []):
                if issue['severity'] in ['CRITICAL', 'HIGH']:
                    plan['short_term_actions'].append({
                        'priority': issue['severity'],
                        'target': f"Medidor {meter_id} ({meter_name})",
                        'category': issue['category'],
                        'problem': issue['issue'],
                        'actions': issue['actions'],
                        'estimated_time': '1-2 horas'
                    })
        
        # Acciones a corto plazo basadas en errores del sistema
        errors = report.get('system_errors', {})
        
        if errors.get('hdlc_boundary', 0) + errors.get('hdlc_checksum', 0) > 15:
            plan['short_term_actions'].append({
                'priority': 'HIGH',
                'target': 'Sistema completo',
                'category': 'PROTOCOL',
                'problem': 'Errores HDLC frecuentes en sistema',
                'actions': [
                    'Revisar configuración global de timeout',
                    'Verificar calidad de conexiones de red',
                    'Considerar actualizar firmware de medidores si disponible',
                    'Implementar retry logic más robusto',
                    'Aumentar intervalo de polling para reducir carga'
                ],
                'estimated_time': '2-4 horas'
            })
        
        if errors.get('socket_closed', 0) > 5:
            plan['short_term_actions'].append({
                'priority': 'HIGH',
                'target': 'Infraestructura de red',
                'category': 'NETWORK',
                'problem': 'Múltiples sockets cerrados inesperadamente',
                'actions': [
                    'Verificar logs de firewall',
                    'Revisar configuración de NAT/Port forwarding',
                    'Verificar estabilidad de switch/router',
                    'Considerar implementar keep-alive TCP',
                    'Revisar límites de conexiones concurrentes en medidores'
                ],
                'estimated_time': '1-3 horas'
            })
        
        # Acciones a largo plazo
        plan['long_term_actions'] = [
            {
                'priority': 'MEDIUM',
                'action': 'Implementar sistema de monitoreo continuo',
                'description': 'Configurar alertas automáticas basadas en métricas QoS',
                'estimated_time': '1 día'
            },
            {
                'priority': 'MEDIUM',
                'action': 'Optimizar configuración de polling',
                'description': 'Ajustar intervalos y timeouts basado en comportamiento real',
                'estimated_time': '4 horas'
            },
            {
                'priority': 'LOW',
                'action': 'Documentar configuración óptima por modelo de medidor',
                'description': 'Crear guía de configuración para diferentes tipos de medidores',
                'estimated_time': '2 días'
            }
        ]
        
        # Medidas preventivas
        plan['preventive_measures'] = [
            {
                'measure': 'Health checks periódicos',
                'description': 'Ejecutar system_health_monitor.py cada hora via cron',
                'implementation': 'Agregar a crontab: 0 * * * * /path/to/system_health_monitor.py --save'
            },
            {
                'measure': 'Backup automático de configuración',
                'description': 'Respaldar base de datos diariamente',
                'implementation': 'Agregar script de backup a cron diario'
            },
            {
                'measure': 'Logs rotativos',
                'description': 'Implementar rotación de logs para evitar llenar disco',
                'implementation': 'Configurar logrotate para journald y logs de aplicación'
            },
            {
                'measure': 'Monitoreo de recursos',
                'description': 'Monitorear CPU, memoria y ancho de banda del servicio',
                'implementation': 'Implementar collectd o similar para métricas del sistema'
            },
            {
                'measure': 'Redundancia de conectividad',
                'description': 'Considerar conexión de respaldo (4G/5G) si red principal falla',
                'implementation': 'Evaluar router con failover automático'
            }
        ]
        
        return plan
    
    def print_action_plan(self, plan: Dict):
        """Imprimir plan de acción formateado"""
        
        priority_icons = {
            'CRITICAL': '🔴',
            'HIGH': '🟠',
            'MEDIUM': '🟡',
            'LOW': '🟢'
        }
        
        print("="*80)
        print("  ACTION PLAN - PLAN DE ACCIÓN PARA MEJORA DEL SISTEMA DLMS")
        print("="*80)
        print(f"📅 Generado: {plan['generated_at']}")
        print(f"📊 Basado en reporte: {plan['based_on_report']}")
        print(f"🏥 Estado del sistema: {plan['system_health']}")
        print()
        
        # Acciones inmediatas
        if plan['immediate_actions']:
            print("🚨 ACCIONES INMEDIATAS (Ejecutar HOY)")
            print("─" * 80)
            for i, action in enumerate(plan['immediate_actions'], 1):
                print(f"\n{priority_icons.get(action['priority'])} Acción #{i} [{action['priority']}]")
                print(f"   Objetivo: {action['target']}")
                print(f"   Acción: {action['action']}")
                print(f"   Tiempo estimado: {action['estimated_time']}")
                print(f"   Impacto: {action['impact']}")
                print(f"\n   Pasos:")
                for step in action['steps']:
                    print(f"      {step}")
            print()
        
        # Acciones a corto plazo
        if plan['short_term_actions']:
            print("\n📋 ACCIONES A CORTO PLAZO (Esta semana)")
            print("─" * 80)
            for i, action in enumerate(plan['short_term_actions'], 1):
                print(f"\n{priority_icons.get(action['priority'])} Acción #{i} [{action['priority']}] - {action['category']}")
                print(f"   Objetivo: {action['target']}")
                print(f"   Problema: {action['problem']}")
                print(f"   Tiempo estimado: {action['estimated_time']}")
                print(f"\n   Acciones recomendadas:")
                for act in action['actions']:
                    print(f"      • {act}")
            print()
        
        # Acciones a largo plazo
        if plan['long_term_actions']:
            print("\n📅 ACCIONES A LARGO PLAZO (Este mes)")
            print("─" * 80)
            for i, action in enumerate(plan['long_term_actions'], 1):
                print(f"\n{priority_icons.get(action['priority'])} {action['action']}")
                print(f"   {action['description']}")
                print(f"   Tiempo estimado: {action['estimated_time']}")
            print()
        
        # Medidas preventivas
        if plan['preventive_measures']:
            print("\n🛡️  MEDIDAS PREVENTIVAS")
            print("─" * 80)
            for i, measure in enumerate(plan['preventive_measures'], 1):
                print(f"\n{i}. {measure['measure']}")
                print(f"   {measure['description']}")
                print(f"   Implementación: {measure['implementation']}")
            print()
        
        print("="*80)
        print("\n💡 RECOMENDACIÓN:")
        print("   1. Ejecutar acciones inmediatas primero (prioridad CRITICAL/HIGH)")
        print("   2. Monitorear mejoras con: python3 system_health_monitor.py")
        print("   3. Implementar medidas preventivas para evitar recurrencia")
        print("   4. Documentar cambios y resultados")
        print()
    
    def save_action_plan(self, plan: Dict, filename: str = None):
        """Guardar plan de acción"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"action_plan_{timestamp}.json"
        
        output_dir = Path("logs/action_plans")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        filepath = output_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(plan, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Action Plan guardado en: {filepath}")
        return filepath


def main():
    """Main entry point"""
    generator = ActionPlanGenerator()
    
    # Cargar último reporte
    report = generator.load_latest_report()
    
    # Generar plan de acción
    plan = generator.generate_action_plan(report)
    
    # Mostrar plan
    generator.print_action_plan(plan)
    
    # Guardar plan
    generator.save_action_plan(plan)


if __name__ == '__main__':
    main()
