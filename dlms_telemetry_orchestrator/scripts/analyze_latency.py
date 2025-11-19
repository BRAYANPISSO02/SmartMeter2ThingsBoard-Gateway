#!/usr/bin/env python3
"""
Analizador de Latencia y Optimizador de Timeouts
Analiza logs y métricas de red para recomendar configuración óptima
"""

import re
import statistics
import subprocess
from typing import List, Tuple, Dict


def analyze_dlms_reading_times() -> Dict:
    """Analizar tiempos de lectura DLMS desde logs"""
    print("📊 Analizando tiempos de lectura DLMS...\n")
    
    # Obtener logs de últimas 24 horas
    cmd = "sudo journalctl -u dlms-multi-meter.service --since '24 hours ago' --no-pager"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    # Extraer tiempos de lectura
    pattern = re.compile(r'\((\d+\.\d+)s\)')
    times = []
    
    for line in result.stdout.split('\n'):
        match = pattern.search(line)
        if match:
            times.append(float(match.group(1)))
    
    if not times:
        print("⚠️  No se encontraron tiempos de lectura en los logs")
        return {}
    
    # Estadísticas
    stats = {
        'count': len(times),
        'min': min(times),
        'max': max(times),
        'mean': statistics.mean(times),
        'median': statistics.median(times),
        'stdev': statistics.stdev(times) if len(times) > 1 else 0,
        'p95': sorted(times)[int(len(times) * 0.95)] if len(times) > 20 else max(times),
        'p99': sorted(times)[int(len(times) * 0.99)] if len(times) > 100 else max(times)
    }
    
    return stats


def analyze_network_latency(host: str) -> Dict:
    """Analizar latencia de red con ping"""
    print(f"🌐 Analizando latencia de red para {host}...")
    
    cmd = f"ping -c 20 {host}"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    # Extraer estadísticas de ping
    pattern = re.compile(r'rtt min/avg/max/mdev = ([\d.]+)/([\d.]+)/([\d.]+)/([\d.]+)')
    match = pattern.search(result.stdout)
    
    if not match:
        return {'error': 'No se pudo obtener latencia'}
    
    return {
        'min_ms': float(match.group(1)),
        'avg_ms': float(match.group(2)),
        'max_ms': float(match.group(3)),
        'mdev_ms': float(match.group(4))
    }


def recommend_timeout(dlms_stats: Dict, network_latency: Dict) -> Dict:
    """Recomendar timeout óptimo basado en análisis"""
    
    if not dlms_stats:
        return {
            'recommended': 10.0,
            'reason': 'Default conservador (sin datos suficientes)'
        }
    
    # Timeout base = P95 de tiempos de lectura + margen de seguridad
    base_timeout = dlms_stats['p95']
    
    # Agregar margen de seguridad (30%)
    safety_margin = base_timeout * 0.3
    
    # Considerar latencia de red
    network_overhead = network_latency.get('avg_ms', 100) / 1000  # Convertir a segundos
    
    # Timeout recomendado
    recommended = base_timeout + safety_margin + network_overhead
    
    # Redondear a 0.5s
    recommended = round(recommended * 2) / 2
    
    # Mínimo 5s, máximo 15s
    recommended = max(5.0, min(15.0, recommended))
    
    return {
        'recommended': recommended,
        'base': base_timeout,
        'safety_margin': safety_margin,
        'network_overhead': network_overhead,
        'reason': f'Basado en P95={base_timeout:.1f}s + margen 30% + latencia red'
    }


def main():
    print("="*80)
    print("  ANÁLISIS DE LATENCIA Y OPTIMIZACIÓN DE TIMEOUTS")
    print("="*80)
    print()
    
    # Analizar tiempos DLMS
    dlms_stats = analyze_dlms_reading_times()
    
    if dlms_stats:
        print(f"✅ Análisis completado: {dlms_stats['count']} lecturas")
        print(f"   Mínimo: {dlms_stats['min']:.2f}s")
        print(f"   Promedio: {dlms_stats['mean']:.2f}s")
        print(f"   Mediana: {dlms_stats['median']:.2f}s")
        print(f"   Máximo: {dlms_stats['max']:.2f}s")
        print(f"   Desv. Estándar: {dlms_stats['stdev']:.2f}s")
        print(f"   P95: {dlms_stats['p95']:.2f}s")
        if dlms_stats['count'] > 100:
            print(f"   P99: {dlms_stats['p99']:.2f}s")
        print()
    
    # Analizar latencia de red para ambos medidores
    print("\n" + "="*80)
    print("  ANÁLISIS DE LATENCIA DE RED")
    print("="*80)
    print()
    
    meter1_latency = analyze_network_latency('192.168.1.127')
    print(f"Medidor 1 (192.168.1.127):")
    if 'error' not in meter1_latency:
        print(f"   Min: {meter1_latency['min_ms']:.1f}ms")
        print(f"   Avg: {meter1_latency['avg_ms']:.1f}ms")
        print(f"   Max: {meter1_latency['max_ms']:.1f}ms")
    print()
    
    meter2_latency = analyze_network_latency('192.168.1.135')
    print(f"Medidor 2 (192.168.1.135):")
    if 'error' not in meter2_latency:
        print(f"   Min: {meter2_latency['min_ms']:.1f}ms")
        print(f"   Avg: {meter2_latency['avg_ms']:.1f}ms")
        print(f"   Max: {meter2_latency['max_ms']:.1f}ms")
    print()
    
    # Usar peor caso de latencia
    worst_latency = meter1_latency
    if 'error' not in meter2_latency:
        if meter2_latency['avg_ms'] > worst_latency.get('avg_ms', 0):
            worst_latency = meter2_latency
    
    # Generar recomendaciones
    print("\n" + "="*80)
    print("  RECOMENDACIONES")
    print("="*80)
    print()
    
    recommendation = recommend_timeout(dlms_stats, worst_latency)
    
    print(f"⚙️  TIMEOUT ACTUAL: 7.0 segundos")
    print(f"✅ TIMEOUT RECOMENDADO: {recommendation['recommended']:.1f} segundos")
    print()
    print(f"📝 Justificación:")
    print(f"   • {recommendation['reason']}")
    if 'base' in recommendation:
        print(f"   • Tiempo base (P95): {recommendation['base']:.1f}s")
        print(f"   • Margen de seguridad (30%): {recommendation['safety_margin']:.1f}s")
        print(f"   • Overhead de red: {recommendation['network_overhead']:.2f}s")
    print()
    
    # Análisis de la situación actual
    if dlms_stats and dlms_stats['p95'] > 7.0:
        print("⚠️  ADVERTENCIA:")
        print(f"   El timeout actual (7.0s) es MENOR que el P95 de tiempos de lectura ({dlms_stats['p95']:.1f}s)")
        print(f"   Esto causa timeouts prematuros en ~{5:.0f}% de las lecturas")
        print(f"   Recomendación: Incrementar timeout a {recommendation['recommended']:.1f}s")
    elif dlms_stats and dlms_stats['max'] > 7.0:
        print("ℹ️  INFORMACIÓN:")
        print(f"   Algunas lecturas ({dlms_stats['max']:.1f}s max) exceden el timeout actual")
        print(f"   Considera incrementar timeout para mayor confiabilidad")
    else:
        print("✅ El timeout actual parece adecuado para las condiciones observadas")
    
    print()
    
    # Recomendaciones adicionales
    print("💡 RECOMENDACIONES ADICIONALES:")
    print()
    
    if worst_latency.get('avg_ms', 0) > 150:
        print("   🔸 Latencia de red alta detectada (>150ms promedio)")
        print("      • Verificar calidad de conexión WiFi/Ethernet")
        print("      • Considerar reducir distancia física o usar cable")
        print("      • Revisar congestión de red")
        print()
    
    if dlms_stats and dlms_stats.get('stdev', 0) > 1.5:
        print("   🔸 Alta variabilidad en tiempos de lectura")
        print("      • Considerar aumentar intervalo de polling")
        print("      • Revisar carga del sistema")
        print("      • Verificar estabilidad de medidores")
        print()
    
    if dlms_stats and dlms_stats['count'] < 50:
        print("   🔸 Pocos datos para análisis robusto")
        print("      • Reejecutar después de 24 horas de operación")
        print("      • Acumular más métricas para mejor análisis")
        print()
    
    # Archivo de configuración sugerido
    print("="*80)
    print("  CONFIGURACIÓN SUGERIDA")
    print("="*80)
    print()
    print("Para aplicar el timeout recomendado, actualizar en:")
    print("  • dlms_poller_production.py: timeout parameter")
    print("  • dlms_client_robust.py: default_timeout")
    print()
    print(f"Valor recomendado: timeout={recommendation['recommended']:.1f}")
    print()
    print("="*80)


if __name__ == '__main__':
    main()
