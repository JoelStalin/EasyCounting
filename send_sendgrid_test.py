#!/usr/bin/env python3
"""
Enviar correo de prueba a Gmail via SendGrid
Test email sender using SendGrid SMTP
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# 🔑 CONFIGURAR AQUI CON TU API KEY DE SENDGRID
SENDGRID_API_KEY = "SG.Tu_API_Key_Aqui"  # Reemplazar con tu clave

if SENDGRID_API_KEY == "SG.Tu_API_Key_Aqui":
    print("")
    print("⚠️  INSTRUCCIONES PARA OBTENER SendGrid API KEY:")
    print("━" * 70)
    print("")
    print("1️⃣  Ir a: https://sendgrid.com/free")
    print("")
    print("2️⃣  Crear cuenta gratuita:")
    print("    Email: joelstalin210@gmail.com")
    print("    Contraseña: [Tu contraseña segura]")
    print("")
    print("3️⃣  Verificar correo en Gmail")
    print("")
    print("4️⃣  Login en: https://app.sendgrid.com")
    print("")
    print("5️⃣  Ir a: Settings → API Keys → Create API Key")
    print("    - Name: DGII_Certification")
    print("    - Permissions: Full Access")
    print("    - Copiar la clave (aparece UNA SOLA VEZ)")
    print("")
    print("6️⃣  Reemplazar en este script:")
    print("    SENDGRID_API_KEY = 'SG.xxxxxxxxxxxxxx'")
    print("")
    print("7️⃣  Ejecutar nuevamente:")
    print("    python send_sendgrid_test.py")
    print("")
    print("━" * 70)
    exit(1)

try:
    print("🔄 Conectando a SendGrid SMTP...")
    server = smtplib.SMTP('smtp.sendgrid.net', 587, timeout=10)
    server.starttls()
    
    print("🔐 Autenticando...")
    server.login('apikey', SENDGRID_API_KEY)
    
    print("✏️  Preparando correo...")
    msg = MIMEMultipart('alternative')
    msg['Subject'] = '✓ Prueba SendGrid - DGII e-CF Certificación'
    msg['From'] = 'sistema@getupsoft.com.do'
    msg['To'] = 'joelstalin210@gmail.com'
    
    text = 'Correo de prueba enviado desde SendGrid. DGII e-CF Certificación.'
    
    html = '''<html><body style="font-family: Arial, sans-serif;">
    <div style="max-width: 600px; margin: 0 auto;">
      <h2 style="color: #25a025;">✓ Correo desde SendGrid SMTP</h2>
      
      <table style="width: 100%; border-collapse: collapse;">
        <tr style="background: #f5f5f5;">
          <td style="padding: 10px;"><strong>Usuario:</strong></td>
          <td style="padding: 10px;">JOEL STALIN</td>
        </tr>
        <tr>
          <td style="padding: 10px;"><strong>RNC:</strong></td>
          <td style="padding: 10px;">25500706423</td>
        </tr>
        <tr style="background: #f5f5f5;">
          <td style="padding: 10px;"><strong>Proyecto:</strong></td>
          <td style="padding: 10px;">DGII e-CF Certificación</td>
        </tr>
        <tr>
          <td style="padding: 10px;"><strong>Status:</strong></td>
          <td style="padding: 10px;"><span style="color: #25a025; font-weight: bold;">✓ Enviado Exitosamente</span></td>
        </tr>
      </table>
      
      <hr style="margin: 20px 0; border: none; border-top: 1px solid #ddd;">
      
      <p style="font-size: 0.9em; color: #666;">
        Este correo fue reenviado por SendGrid desde tu aplicación FastAPI.<br>
        Si recibes este correo, la configuración SMTP está funcionando correctamente.
      </p>
      
      <p style="font-size: 0.85em; color: #999;">
        Timestamp: ''' + __import__('datetime').datetime.now().isoformat() + '''
      </p>
    </div>
    </body></html>'''
    
    part1 = MIMEText(text, 'plain')
    part2 = MIMEText(html, 'html')
    msg.attach(part1)
    msg.attach(part2)
    
    print("📤 Enviando correo...")
    server.sendmail('sistema@getupsoft.com.do', 'joelstalin210@gmail.com', msg.as_string())
    server.quit()
    
    print("")
    print("╔" + "═" * 68 + "╗")
    print("║" + " ✓ ¡CORREO ENVIADO A GMAIL EXITOSAMENTE! ".center(68) + "║")
    print("╚" + "═" * 68 + "╝")
    print("")
    print("📬 PRÓXIMOS PASOS:")
    print("   1. Abrir Gmail: https://mail.google.com")
    print("   2. Login: joelstalin210@gmail.com")
    print("   3. Buscar asunto: '✓ Prueba SendGrid'")
    print("   4. Verificar que el correo llegó correctamente")
    print("")
    print("✅ Si ves el correo en Gmail = SMTP está listo para producción")
    print("")
    
except smtplib.SMTPAuthenticationError as e:
    print("")
    print("❌ ERROR DE AUTENTICACIÓN")
    print(f"   Detalles: {e}")
    print("")
    print("   Verificar:")
    print("   1. SendGrid API Key es correcta")
    print("   2. Cuenta SendGrid está verificada")
    print("   3. API Key tiene permisos suficientes")
    print("")
    
except smtplib.SMTPException as e:
    print(f"❌ Error SMTP: {e}")
    
except Exception as e:
    print(f"❌ Error: {e}")
    print("")
    print("Verificar:")
    print("  - Conexión a internet")
    print("  - Firewall permite conexión a smtp.sendgrid.net:587")
