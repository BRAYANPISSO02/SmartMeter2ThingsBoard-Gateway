#!/usr/bin/env python3
"""
Diagnóstico Avanzado del Medidor 2
Pruebas exhaustivas para identificar causa raíz del fallo
"""

import socket
import time
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dlms_reader import DLMSClient


def test_tcp_connection(host: str, port: int, timeout: float = 5.0) -> dict:
    """Probar conexión TCP básica"""
    print(f"\n1️⃣  Probando conexión TCP a {host}:{port}...")
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        
        start = time.time()
        result = sock.connect_ex((host, port))
        elapsed = time.time() - start
        
        sock.close()
        
        if result == 0:
            print(f"   ✅ Conexión TCP exitosa ({elapsed*1000:.0f}ms)")
            return {'success': True, 'time_ms': elapsed*1000}
        else:
            print(f"   ❌ Conexión TCP falló: Error {result}")
            return {'success': False, 'error': result}
            
    except Exception as e:
        print(f"   ❌ Excepción: {e}")
        return {'success': False, 'error': str(e)}


def test_tcp_persistence(host: str, port: int, duration: float = 10.0) -> dict:
    """Probar si el socket permanece abierto"""
    print(f"\n2️⃣  Probando persistencia de conexión TCP ({duration}s)...")
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(duration + 1)
        
        sock.connect((host, port))
        print(f"   ✅ Socket conectado")
        
        # Esperar sin enviar datos
        start = time.time()
        time.sleep(duration)
        elapsed = time.time() - start
        
        # Intentar enviar byte de prueba
        try:
            sock.send(b'\x00')
            print(f"   ✅ Socket sigue abierto después de {elapsed:.1f}s")
            success = True
        except:
            print(f"   ❌ Socket cerrado por el servidor después de {elapsed:.1f}s")
            success = False
        
        sock.close()
        return {'success': success, 'duration': elapsed}
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return {'success': False, 'error': str(e)}


def test_dlms_handshake(host: str, port: int, verbose: bool = True) -> dict:
    """Probar handshake DLMS completo"""
    print(f"\n3️⃣  Probando handshake DLMS...")
    
    try:
        client = DLMSClient(
            host=host,
            port=port,
            client_sap=1,
            server_logical=0,
            server_physical=1,
            password=b'22222222',
            timeout=10.0,
            max_info_length=None,
            verbose=verbose
        )
        
        print(f"   🔌 Intentando conectar...")
        client.connect()
        print(f"   ✅ Handshake DLMS exitoso")
        
        # Intentar lectura de prueba
        print(f"   📖 Intentando lectura de prueba (voltage)...")
        result = client.read_register('1-1:32.7.0')
        
        if result is not None:
            print(f"   ✅ Lectura exitosa: {result}")
        else:
            print(f"   ⚠️  Lectura retornó None")
        
        client.disconnect()
        return {'success': True, 'reading': result}
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        if verbose:
            traceback.print_exc()
        return {'success': False, 'error': str(e)}


def test_alternative_credentials(host: str, port: int) -> dict:
    """Probar credenciales alternativas comunes"""
    print(f"\n4️⃣  Probando credenciales alternativas...")
    
    # Credenciales comunes
    credentials = [
        {'client_sap': 16, 'server_logical': 0, 'server_physical': 1, 'password': b'22222222', 'desc': 'client_sap=16'},
        {'client_sap': 1, 'server_logical': 1, 'server_physical': 1, 'password': b'22222222', 'desc': 'server_logical=1'},
        {'client_sap': 1, 'server_logical': 0, 'server_physical': 0, 'password': b'22222222', 'desc': 'server_physical=0'},
        {'client_sap': 1, 'server_logical': 0, 'server_physical': 1, 'password': b'00000000', 'desc': 'password=00000000'},
        {'client_sap': 1, 'server_logical': 0, 'server_physical': 1, 'password': b'', 'desc': 'sin password'},
    ]
    
    for cred in credentials:
        print(f"   🔑 Probando: {cred['desc']}...")
        
        try:
            client = DLMSClient(
                host=host,
                port=port,
                client_sap=cred['client_sap'],
                server_logical=cred['server_logical'],
                server_physical=cred['server_physical'],
                password=cred['password'],
                timeout=5.0,
                max_info_length=None,
                verbose=False
            )
            
            client.connect()
            print(f"      ✅ ÉXITO con {cred['desc']}")
            client.disconnect()
            return {'success': True, 'credentials': cred}
            
        except Exception as e:
            print(f"      ❌ Falló: {str(e)[:50]}")
    
    print(f"   ❌ Ninguna credencial alternativa funcionó")
    return {'success': False}


def test_timing_sensitivity(host: str, port: int) -> dict:
    """Probar sensibilidad a timing (delays entre frames)"""
    print(f"\n5️⃣  Probando sensibilidad a delays...")
    
    delays = [0.0, 0.5, 1.0, 2.0]
    
    for delay in delays:
        print(f"   ⏱️  Probando con delay de {delay}s...")
        
        try:
            # Aquí necesitaríamos modificar DLMSClient para agregar delays
            # Por ahora solo probamos conexión básica con timeout diferente
            client = DLMSClient(
                host=host,
                port=port,
                client_sap=1,
                server_logical=0,
                server_physical=1,
                password=b'22222222',
                timeout=10.0 + delay,
                max_info_length=None,
                verbose=False
            )
            
            time.sleep(delay)  # Delay antes de conectar
            client.connect()
            print(f"      ✅ Funciona con delay {delay}s")
            client.disconnect()
            return {'success': True, 'optimal_delay': delay}
            
        except Exception as e:
            print(f"      ❌ Falló: {str(e)[:40]}")
    
    return {'success': False}


def main():
    print("="*80)
    print("  DIAGNÓSTICO AVANZADO - MEDIDOR 2 (192.168.1.135:3333)")
    print("="*80)
    
    HOST = '192.168.1.135'
    PORT = 3333
    
    results = {}
    
    # Test 1: TCP Connection
    results['tcp'] = test_tcp_connection(HOST, PORT)
    
    if not results['tcp']['success']:
        print("\n❌ DIAGNÓSTICO: TCP no conecta - problema de red/firewall")
        print("   Acciones:")
        print("   • Verificar que medidor esté encendido")
        print("   • Verificar firewall en medidor")
        print("   • Verificar ruta de red")
        return
    
    # Test 2: TCP Persistence
    results['persistence'] = test_tcp_persistence(HOST, PORT, duration=5.0)
    
    if not results['persistence']['success']:
        print("\n⚠️  OBSERVACIÓN: Medidor cierra socket rápidamente")
        print("   Posible timeout agresivo en el medidor")
    
    # Test 3: DLMS Handshake
    results['dlms'] = test_dlms_handshake(HOST, PORT, verbose=True)
    
    if results['dlms']['success']:
        print("\n✅ ¡ÉXITO! El medidor SÍ funciona correctamente")
        print("   El problema puede ser intermitente o de timing")
        return
    
    # Test 4: Alternative Credentials
    results['credentials'] = test_alternative_credentials(HOST, PORT)
    
    if results['credentials']['success']:
        print("\n✅ ¡SOLUCIÓN ENCONTRADA!")
        print(f"   Usar credenciales: {results['credentials']['credentials']}")
        return
    
    # Test 5: Timing Sensitivity
    results['timing'] = test_timing_sensitivity(HOST, PORT)
    
    if results['timing']['success']:
        print("\n✅ ¡SOLUCIÓN ENCONTRADA!")
        print(f"   Medidor requiere delay de {results['timing']['optimal_delay']}s")
        return
    
    # Resumen final
    print("\n" + "="*80)
    print("  DIAGNÓSTICO FINAL")
    print("="*80)
    print()
    print("❌ No se pudo establecer comunicación DLMS con el medidor")
    print()
    print("Causas probables:")
    print("   1. Medidor requiere credenciales específicas no probadas")
    print("   2. Medidor en modo incompatible (diferente a Meter 1)")
    print("   3. Problema de firmware en el medidor")
    print("   4. Medidor siendo accedido por otro sistema")
    print("   5. Medidor requiere configuración especial previa")
    print()
    print("Próximos pasos:")
    print("   • Consultar manual del medidor para credenciales correctas")
    print("   • Verificar si hay software propietario conectado")
    print("   • Considerar reset de fábrica del medidor")
    print("   • Contactar fabricante para soporte técnico")
    print()
    print("="*80)


if __name__ == '__main__':
    main()
