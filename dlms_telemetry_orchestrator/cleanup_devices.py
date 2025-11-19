#!/usr/bin/env python3
"""
Script para limpiar dispositivos duplicados en ThingsBoard
Mantiene solo los dispositivos activos del sistema multi-meter actual
"""

import requests
import sys

# Configuración
TB_HOST = "localhost"
TB_PORT = 8080
USERNAME = "tenant@thingsboard.org"
PASSWORD = "tenant"

# Dispositivos a ELIMINAR (los obsoletos/duplicados)
DEVICES_TO_DELETE = [
    "DLMS-Meter-02",  # Obsoleto, creado antes del sistema multi-meter
    "DLMS-Meter-01"   # Obsoleto, era el único medidor antes
]

# Dispositivos a MANTENER (los actuales)
DEVICES_TO_KEEP = [
    "medidor_dlms_principal",  # Medidor 1 actual
    "Medidor_DLMS_02",          # Medidor 2 actual
    "DLMS-BRIDGE"               # Gateway
]

def login():
    """Login a ThingsBoard y obtener token"""
    url = f"http://{TB_HOST}:{TB_PORT}/api/auth/login"
    data = {"username": USERNAME, "password": PASSWORD}
    
    try:
        response = requests.post(url, json=data, timeout=5)
        response.raise_for_status()
        return response.json()["token"]
    except Exception as e:
        print(f"❌ Error en login: {e}")
        sys.exit(1)

def get_devices(token):
    """Obtener lista de todos los dispositivos"""
    url = f"http://{TB_HOST}:{TB_PORT}/api/tenant/devices?pageSize=100&page=0"
    headers = {"X-Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(url, headers=headers, timeout=5)
        response.raise_for_status()
        return response.json()["data"]
    except Exception as e:
        print(f"❌ Error obteniendo dispositivos: {e}")
        return []

def delete_device(token, device_id, device_name):
    """Eliminar un dispositivo"""
    url = f"http://{TB_HOST}:{TB_PORT}/api/device/{device_id}"
    headers = {"X-Authorization": f"Bearer {token}"}
    
    try:
        response = requests.delete(url, headers=headers, timeout=5)
        response.raise_for_status()
        print(f"  ✅ Eliminado: {device_name}")
        return True
    except Exception as e:
        print(f"  ❌ Error eliminando {device_name}: {e}")
        return False

def main():
    print("=" * 80)
    print("LIMPIEZA DE DISPOSITIVOS EN THINGSBOARD")
    print("=" * 80)
    print()
    
    # Login
    print("🔐 Autenticando...")
    token = login()
    print("✅ Autenticado correctamente")
    print()
    
    # Obtener dispositivos
    print("📋 Obteniendo lista de dispositivos...")
    devices = get_devices(token)
    print(f"✅ Encontrados {len(devices)} dispositivos")
    print()
    
    # Mostrar dispositivos actuales
    print("Dispositivos actuales:")
    print("-" * 80)
    for dev in devices:
        status = "🟢 MANTENER" if dev["name"] in DEVICES_TO_KEEP else "🔴 ELIMINAR"
        print(f"{status}: {dev['name']} (Type: {dev['type']})")
    print()
    
    # Confirmar (auto-confirmado para ejecución automática)
    print("=" * 80)
    print(f"Se eliminarán {len(DEVICES_TO_DELETE)} dispositivos:")
    for name in DEVICES_TO_DELETE:
        print(f"  • {name}")
    print()
    print("✅ Auto-confirmado, procediendo con la eliminación...")
    print()
    print("🗑️  Eliminando dispositivos obsoletos...")
    print("-" * 80)
    
    # Eliminar dispositivos
    deleted_count = 0
    for dev in devices:
        if dev["name"] in DEVICES_TO_DELETE:
            if delete_device(token, dev["id"]["id"], dev["name"]):
                deleted_count += 1
    
    print()
    print("=" * 80)
    print(f"✅ Limpieza completada: {deleted_count} dispositivos eliminados")
    print()
    
    # Mostrar dispositivos restantes
    print("📋 Dispositivos restantes:")
    devices = get_devices(token)
    for dev in devices:
        print(f"  • {dev['name']} (Type: {dev['type']})")
    
    print()
    print("=" * 80)

if __name__ == "__main__":
    main()
