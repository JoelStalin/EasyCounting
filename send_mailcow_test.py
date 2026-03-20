#!/usr/bin/env python3
"""
Test Email Sender via Mailcow
Envía correo de prueba usando Mailcow SMTP
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
import os
from dotenv import load_dotenv

# Cargar .env.local
load_dotenv('.env.local')

def send_test_email():
    """Send test email via Mailcow"""
    
    print("╔" + "═" * 68 + "╗")
    print("║" + " 📧 TEST EMAIL VIA MAILCOW ".center(68) + "║")
    print("╚" + "═" * 68 + "╝")
    print()
    
    # Configuración
    smtp_host = os.getenv('SMTP_HOST', 'localhost')
    smtp_port = int(os.getenv('SMTP_PORT', 587))
    smtp_user = os.getenv('SMTP_USER', '')
    smtp_pass = os.getenv('SMTP_PASS', '')
    smtp_from = os.getenv('SMTP_FROM', 'sistema@getupsoft.com.do')
    smtp_secure = os.getenv('SMTP_SECURE', 'true').lower() == 'true'
    
    print("📋 Configuración SMTP:")
    print(f"   Host: {smtp_host}:{smtp_port}")
    print(f"   TLS: {smtp_secure}")
    print(f"   From: {smtp_from}")
    print()
    
    # Validar
    if not smtp_user or not smtp_pass:
        print("❌ ERROR: SMTP_USER o SMTP_PASS no configurados en .env.local")
        print()
        print("Agregar a .env.local:")
        print("─" * 68)
        print("SMTP_HOST=mailcow-postfix  # o localhost")
        print("SMTP_PORT=587")
        print("SMTP_USER=sistema@getupsoft.com.do")
        print("SMTP_PASS=tu_contraseña_mailcow")
        print("SMTP_SECURE=true")
        print("SMTP_FROM=sistema@getupsoft.com.do")
        print("─" * 68)
        return False
    
    try:
        print("🔄 Conectando a Mailcow SMTP...")
        server = smtplib.SMTP(smtp_host, smtp_port, timeout=10)
        
        if smtp_secure:
            print("🔐 Iniciando TLS...")
            server.starttls()
        
        print("🔑 Autenticando...")
        server.login(smtp_user, smtp_pass)
        
        print("✏️  Preparando correo...")
        msg = MIMEMultipart('alternative')
        msg['Subject'] = '✓ Prueba Mailcow - DGII e-CF'
        msg['From'] = smtp_from
        msg['To'] = 'joelstalin210@gmail.com'
        
        text = 'Correo de prueba enviado desde Mailcow. DGII e-CF Certificación.'
        
        html = '''<html><body style="font-family: Arial, sans-serif;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
          <h2 style="color: #25a025;">✓ Correo desde Mailcow</h2>
          
          <div style="background: #f5f5f5; padding: 15px; border-radius: 5px; margin: 20px 0;">
            <table style="width: 100%;">
              <tr>
                <td><strong>Usuario:</strong></td>
                <td>JOEL STALIN</td>
              </tr>
              <tr style="background: white;">
                <td><strong>RNC:</strong></td>
                <td>25500706423</td>
              </tr>
              <tr>
                <td><strong>Proyecto:</strong></td>
                <td>DGII e-CF Certificación</td>
              </tr>
              <tr style="background: white;">
                <td><strong>Sistema de Correos:</strong></td>
                <td><span style="color: #25a025; font-weight: bold;">✓ Mailcow Self-Hosted</span></td>
              </tr>
              <tr>
                <td><strong>Status:</strong></td>
                <td><span style="color: #25a025; font-weight: bold;">Enviado Exitosamente</span></td>
              </tr>
            </table>
          </div>
          
          <hr style="margin: 20px 0; border: none; border-top: 1px solid #ddd;">
          
          <p style="font-size: 0.9em; color: #666;">
            Este correo fue reenviado por Mailcow desde tu aplicación FastAPI.<br>
            Si recibes este correo, el sistema está funcionando correctamente.
          </p>
          
          <p style="font-size: 0.85em; color: #999; margin-top: 30px;">
            Mailcow es la solución completa self-hosted para correos electrónicos.
          </p>
        </div>
        </body></html>'''
        
        part1 = MIMEText(text, 'plain')
        part2 = MIMEText(html, 'html')
        msg.attach(part1)
        msg.attach(part2)
        
        print("📤 Enviando correo...")
        server.sendmail(smtp_from, 'joelstalin210@gmail.com', msg.as_string())
        server.quit()
        
        print()
        print("╔" + "═" * 68 + "╗")
        print("║" + " ✅ CORREO ENVIADO EXITOSAMENTE VIA MAILCOW ".center(68) + "║")
        print("╚" + "═" * 68 + "╝")
        print()
        print("📬 PRÓXIMOS PASOS:")
        print("   1. Revisar Gmail: https://mail.google.com")
        print("   2. Buscar asunto: '✓ Prueba Mailcow'")
        print("   3. Verificar que el correo llegó")
        print()
        print("💻 Ver en Mailcow Webmail:")
        print("   https://localhost/mail")
        print("   Usuario: sistema@getupsoft.com.do")
        print("   Contraseña: [Tu contraseña Mailcow]")
        print()
        
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        print()
        print(f"❌ Error de autenticación: {e}")
        print()
        print("Verificar:")
        print("  1. SMTP_USER es correcto (ej: sistema@getupsoft.com.do)")
        print("  2. SMTP_PASS es la contraseña de Mailcow (no la del sistema)")
        print("  3. Usuario existe en Mailcow")
        return False
        
    except smtplib.SMTPException as e:
        print(f"❌ Error SMTP: {e}")
        print()
        print("Verificar:")
        print("  1. Mailcow está levantado: docker-compose ps")
        print("  2. SMTP_HOST es correcto (localhost o mailcow-postfix)")
        print("  3. SMTP_PORT es 587 para TLS")
        return False
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print()
        print("Verificar:")
        print("  1. Conexión a internet")
        print("  2. Firewall permite localhost:587")
        print("  3. .env.local tiene SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS")
        return False


if __name__ == '__main__':
    success = send_test_email()
    exit(0 if success else 1)
