#!/usr/bin/env python3
"""
Script para iniciar Mailpit y ejecutar pruebas de email
"""

import subprocess
import time
import sys
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent

def run_command(cmd, description):
    """Ejecutar comando y mostrar resultado"""
    print(f"\n[*] {description}...")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"[OK] {description} - Exitoso")
            return True
        else:
            print(f"[ERROR] {description} - Falló")
            print(result.stderr)
            return False
    except Exception as e:
        print(f"[ERROR] {description} - Exception: {e}")
        return False

def main():
    """Flujo principal"""
    
    print("╔════════════════════════════════════════╗")
    print("║   MAILPIT EMAIL TEST AUTOMATION       ║")
    print("║   DGII e-CF Certificacion             ║")
    print("╚════════════════════════════════════════╝")
    
    os.chdir(PROJECT_ROOT)
    
    # Paso 1: Levantar Docker Compose
    print("\n[PASO 1] Levantando Docker Compose...")
    if not run_command("docker-compose up -d mailpit", "Iniciando Mailpit en Docker"):
        print("\n⚠️  No se pudo iniciar Mailpit. Asegúrate de que Docker está instalado.")
        print("Instalación: https://docs.docker.com/get-docker/")
        return 1
    
    # Paso 2: Esperar a que Mailpit esté listo
    print("\n[PASO 2] Esperando a que Mailpit esté listo...")
    max_attempts = 30
    for attempt in range(max_attempts):
        try:
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(('127.0.0.1', 1025))
            sock.close()
            if result == 0:
                print("[OK] Mailpit está listo en puerto 1025")
                break
            print(f"    Intentando... {attempt + 1}/{max_attempts}")
            time.sleep(1)
        except:
            time.sleep(1)
    else:
        print("[ERROR] Mailpit no respondió en tiempo esperado")
        return 1
    
    # Paso 3: Esperar un poco más
    print("\n[PASO 3] Esperando 2 segundos más...")
    time.sleep(2)
    
    # Paso 4: Enviar prueba de email
    print("\n[PASO 4] Enviando correo de prueba...")
    
    email_script = PROJECT_ROOT / "send_email_simple_test.py"
    if email_script.exists():
        # Actualizamos el script temporalmente para usar mailpit
        # o llamamos directamente con SMTP
        cmd = f"python {email_script}"
        if not run_command(cmd, "Enviando correo vía SMTP a Mailpit"):
            print("\n⚠️  Nota: El envío falló pero Mailpit sigue disponible.")
            print("    Puedes ver la Web UI en: http://localhost:8025")
            return 1
    
    # Paso 5: Confirmación
    print("\n═════════════════════════════════════════════════════════")
    print("[OK] PRUEBA COMPLETADA EXITOSAMENTE")
    print("═════════════════════════════════════════════════════════")
    
    print("\n📧 Información de Mailpit:")
    print("  - SMTP: localhost:1025")
    print("  - Web UI: http://localhost:8025")
    print("  - Usuario: (sin autenticación)")
    print("  - Contraseña: (sin autenticación)")
    
    print("\n📺 Abre en tu navegador para ver los correos:")
    print("  → http://localhost:8025")
    
    print("\n💡 Comandos útiles:")
    print("  - Ver logs: docker-compose logs -f mailpit")
    print("  - Detener: docker-compose stop mailpit")
    print("  - Reiniciar: docker-compose restart mailpit")
    
    print("\n✅ Estado: MAILPIT LISTO PARA USAR")
    print("\nSiguiente paso: Continuar con certificación DGII")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
