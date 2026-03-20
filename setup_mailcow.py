#!/usr/bin/env python3
"""
Mailcow Automation Setup
Configuración automática de Mailcow para DGII e-CF
"""
import os
import json
from pathlib import Path
import subprocess
import time

def setup_mailcow():
    """Configure Mailcow automatically"""
    
    print("╔" + "═" * 70 + "╗")
    print("║" + " 📧 CONFIGURACIÓN AUTOMÁTICA MAILCOW ".center(70) + "║")
    print("║" + " DGII e-CF Certificación ".center(70) + "║")
    print("╚" + "═" * 70 + "╝")
    print()
    
    mailcow_dir = Path("mailcow")
    
    if not mailcow_dir.exists():
        print("❌ Mailcow no encontrado")
        print("   Ejecutar: git clone https://github.com/mailcow/mailcow-dockerized mailcow")
        return False
    
    print("✓ Directorio Mailcow encontrado")
    print()
    
    # Step 1: Create .env for Mailcow
    print("[1/5] 🔧 Creando configuración Mailcow...")
    
    mailcow_env = mailcow_dir / ".env"
    
    if not mailcow_env.exists():
        env_content = """COMPOSE_PROJECT_NAME=mailcow
MAILCOW_HOSTNAME=mail.getupsoft.com.do
MAILCOW_TZ=America/Santo_Domingo
MAILCOW_DOCKER_LABELS=com.example=mailcow
LOG_LINES=9999
SKIP_CLAMD=n
SKIP_IP_CHECK=n
SKIP_EXTERNAL_CHECKS=n
SKIP_SOGO=n
ENABLE_SSL_SNI=y
ENABLE_TLS_SNI=y
"""
        mailcow_env.write_text(env_content)
        print("      ✓ .env creado")
    else:
        print("      ✓ .env ya existe")
    
    print()
    
    # Step 2: Check docker-compose
    print("[2/5] 📦 Verificando docker-compose...")
    mailcow_compose = mailcow_dir / "docker-compose.yml"
    
    if mailcow_compose.exists():
        print("      ✓ docker-compose.yml encontrado")
    else:
        print("      ❌ Error: docker-compose.yml no encontrado en mailcow/")
        return False
    
    print()
    
    # Step 3: Show startup commands
    print("[3/5] 🚀 Comandos para iniciar Mailcow...")
    print()
    print("      cd c:\\Users\\yoeli\\Documents\\dgii_encf\\mailcow")
    print("      docker-compose up -d")
    print()
    
    # Step 4: Configuration info
    print("[4/5] 📋 Información de Acceso...")
    print()
    print("      Webmail (SOGo):")
    print("      └─ https://localhost/mail")
    print("         Usuario: sistema@getupsoft.com.do")
    print("         Contraseña: [la que configures]")
    print()
    print("      Admin Panel:")
    print("      └─ https://localhost/admin")
    print("         Usuario: admin")
    print("         Contraseña: moohoo (cambiar después)")
    print()
    
    # Step 5: .env.local Configuration
    print("[5/5] 🔐 Configurar en .env.local...")
    print()
    
    env_local = Path(".env.local")
    
    if env_local.exists():
        content = env_local.read_text()
        
        # Check if already configured
        if "SMTP_HOST=mailcow" in content:
            print("      ✓ Ya configurado para Mailcow")
        else:
            print("      ⚠️  Necesita actualizar .env.local:")
            print()
            print("      Agregar o actualizar:")
            print("      ─" * 35)
            print("      SMTP_HOST=mailcow-postfix")
            print("      SMTP_PORT=587")
            print("      SMTP_USER=sistema@getupsoft.com.do")
            print("      SMTP_PASS=tu_contraseña_mailcow")
            print("      SMTP_SECURE=true")
            print("      SMTP_FROM=sistema@getupsoft.com.do")
            print("      ─" * 35)
    else:
        print("      ❌ .env.local no encontrado")
    
    print()
    print()
    print("╔" + "═" * 70 + "╗")
    print("║" + " ✅ SETUP COMPLETADO ".center(70) + "║")
    print("╚" + "═" * 70 + "╝")
    print()
    print("📌 PRÓXIMOS PASOS:")
    print()
    print("  1. Actualizar .env.local con credenciales Mailcow")
    print("  2. Ejecutar: cd mailcow && docker-compose up -d")
    print("  3. Esperar 2-3 minutos para que levante")
    print("  4. Crear usuario en Admin: https://localhost/admin")
    print("  5. Revisar SMTP desde app: python send_mailcow_test.py")
    print()
    
    return True


if __name__ == "__main__":
    setup_mailcow()
