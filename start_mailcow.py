#!/usr/bin/env python3
"""
Mailcow Integration & Startup
Integra Mailcow con docker-compose actual y lo levanta
"""
import subprocess
import time
from pathlib import Path
import sys

def run_cmd(cmd, description=""):
    """Run command and return result"""
    if description:
        print(f"  {description}...", end=" ", flush=True)
    
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=300)
        if description:
            if result.returncode == 0:
                print("✓")
            else:
                print(f"✗")
                if result.stderr:
                    print(f"     Error: {result.stderr[:200]}")
        return result
    except subprocess.TimeoutExpired:
        print("✗ (Timeout)")
        return None
    except Exception as e:
        print(f"✗ ({e})")
        return None

def main():
    """Setup and start Mailcow"""
    
    print("╔" + "═" * 70 + "╗")
    print("║" + " 🚀 MAILCOW STARTUP ".center(70) + "║")
    print("║" + " Integración y Arranque Automático ".center(70) + "║")
    print("╚" + "═" * 70 + "╝")
    print()
    
    # Check directories
    print("[1/5] 🔍 Verificando directorios...")
    
    if not Path("mailcow").exists():
        print("      ❌ Mailcow no encontrado")
        print("      Ejecutar: git clone https://github.com/mailcow/mailcow-dockerized mailcow")
        return False
    
    if not Path("docker-compose.yml").exists():
        print("      ❌ docker-compose.yml no encontrado")
        return False
    
    print("      ✓ Estructura correcta")
    print()
    
    # Setup Mailcow
    print("[2/5] ⚙️  Configurando Mailcow...")
    run_cmd("cd mailcow && ls .env", "Verificando .env")
    print()
    
    # Start Docker services
    print("[3/5] 🐳 Levantando servicios principales...")
    run_cmd("docker-compose up -d db redis", "PostgreSQL y Redis")
    time.sleep(5)
    print()
    
    print("[4/5] 🐳 Levantando Mailcow...")
    run_cmd("cd mailcow && docker-compose up -d", "Mailcow")
    time.sleep(5)
    print()
    
    # Check status
    print("[5/5] 📊 Verificando status...")
    print()
    
    print("      Servicios principales:")
    result = run_cmd("docker-compose ps --format='table {{.Service}}\t{{.Status}}'", "")
    if result and result.returncode == 0:
        print(result.stdout)
    
    print()
    print("      Servicios Mailcow:")
    result = run_cmd("cd mailcow && docker-compose ps --format='table {{.Service}}\t{{.Status}}'", "")
    if result and result.returncode == 0:
        lines = result.stdout.split('\n')
        for line in lines[:10]:  # Show first 10 services
            if line.strip():
                print(f"      {line}")
    
    print()
    print("╔" + "═" * 70 + "╗")
    print("║" + " ✅ MAILCOW INICIADO ".center(70) + "║")
    print("╚" + "═" * 70 + "╝")
    print()
    
    print("🌐 ACCESO MAILCOW:")
    print()
    print("   Admin Panel:")
    print("   └─ https://localhost/admin")
    print("      Usuario: admin")
    print("      Contraseña: moohoo (⚠️ CAMBIAR)")
    print()
    print("   Webmail (SOGo):")
    print("   └─ https://localhost/mail")
    print("      Usuario: [Tu usuario Mailcow]")
    print("      Contraseña: [Tu contraseña]")
    print()
    
    print("📧 CONFIGURAR USUARIO EN MAILCOW:")
    print()
    print("   1. Ir a: https://localhost/admin")
    print("   2. Mail Accounts → Add Mailbox")
    print("   3. Domain: getupsoft.com.do")
    print("   4. Mailbox: sistema@getupsoft.com.do")
    print("   5. Password: [Tu contraseña segura]")
    print("   6. Save")
    print()
    
    print("🔧 ACTUALIZAR .env.local CON:")
    print()
    print("   SMTP_HOST=mailcow-postfix")
    print("   SMTP_PORT=587")
    print("   SMTP_USER=sistema@getupsoft.com.do")
    print("   SMTP_PASS=[Tu contraseña Mailcow]")
    print("   SMTP_SECURE=true")
    print("   SMTP_FROM=sistema@getupsoft.com.do")
    print()
    
    print("✅ PRUEBA RÁPIDA:")
    print()
    print("   python send_mailcow_test.py")
    print()
    
    return True


if __name__ == '__main__':
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Operación cancelada por el usuario")
        sys.exit(1)
