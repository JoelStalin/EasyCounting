#!/usr/bin/env python3
"""
Script simple para enviar correo de prueba sin dependencias de app.
Demuestra que el SMTP está funcionando.
"""

import smtplib
import sys
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
import os
from dotenv import load_dotenv

# Cargar variables de entorno
env_path = Path(__file__).resolve().parent / ".env.local"
load_dotenv(env_path)

# Configuración SMTP desde variables de entorno
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.mailtrap.io")
SMTP_PORT = int(os.getenv("SMTP_PORT", "465"))
SMTP_USER = os.getenv("SMTP_USER", "1a2b3c4d5e6f7g")
SMTP_PASS = os.getenv("SMTP_PASS", "8h9i0j1k2l3m4n")
SMTP_FROM = os.getenv("SMTP_FROM", "prueba-dgii@getupsoft.com.do")

# Información del usuario
USUARIO = "JOEL STALIN"
RNC = "25500706423"
EMAIL_DESTINO = "joelstalin210@gmail.com"

def send_test_email():
    """Enviar correo de prueba"""
    
    print("[*] Iniciando envío de correo de prueba...")
    print(f"    Usuario: {USUARIO} (RNC: {RNC})")
    print(f"    Destino: {EMAIL_DESTINO}")
    print(f"    Servidor SMTP: {SMTP_HOST}:{SMTP_PORT}")
    
    try:
        # Crear mensaje
        message = MIMEMultipart()
        message['From'] = SMTP_FROM
        message['To'] = EMAIL_DESTINO
        message['Subject'] = "DGII e-CF PRUEBA EN VIVO - Certificacion"
        
        # Cuerpo HTML
        html_body = f"""
        <html>
          <body style="font-family: Arial, sans-serif;">
            <h2 style="color: #2c3e50;">Prueba de Certificacion DGII e-CF</h2>
            <p><strong>Usuario:</strong> {USUARIO}</p>
            <p><strong>RNC:</strong> {RNC}</p>
            <p><strong>Email:</strong> {EMAIL_DESTINO}</p>
            <hr>
            <p>Este correo demuestra que el sistema SMTP funciona correctamente.</p>
            <p style="color: #27ae60; font-weight: bold;">✓ Sistema SMTP: FUNCIONANDO</p>
            <p><small>Enviado desde: Certificacion en Vivo DGII e-CF</small></p>
          </body>
        </html>
        """
        
        text_body = f"""
Prueba de Certificacion DGII e-CF

Usuario: {USUARIO}
RNC: {RNC}
Email: {EMAIL_DESTINO}

Este correo demuestra que el sistema SMTP funciona correctamente.
Sistema SMTP: FUNCIONANDO

Enviado desde: Certificacion en Vivo DGII e-CF
        """
        
        # Agregar contenido
        message.attach(MIMEText(text_body, 'plain'))
        message.attach(MIMEText(html_body, 'html'))
        
        # Enviar vía SMTP
        print(f"\n[*] Conectando a {SMTP_HOST}:{SMTP_PORT}...")
        
        if SMTP_PORT == 465:
            import ssl
            context = ssl.create_default_context()
            server = smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=context)
        else:
            # Usar STARTTLS para puerto 2525 (Mailtrap)
            server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
            server.starttls()
        
        print("[*] Autenticando...")
        server.login(SMTP_USER, SMTP_PASS)
        
        print("[*] Enviando correo...")
        server.send_message(message)
        server.quit()
        
        print("\n[ OK ] Correo enviado exitosamente!")
        print(f"[ OK ] Revisar bandeja de entrada en: {EMAIL_DESTINO}")
        print("\n✓ PRUEBA FUNCIONAL COMPLETADA")
        return 0
        
    except Exception as e:
        print(f"\n[ERROR] Fallo al enviar correo: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(send_test_email())
