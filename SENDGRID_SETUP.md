# 🚀 Integración SendGrid para Correos Externos

## Preparación Rápida (5 minutos)

### 1️⃣ Crear Cuenta SendGrid (Gratuita para Desarrollo)

```bash
# Ir a: https://sendgrid.com/free
# Registrar con Gmail: joelstalin210@gmail.com
# Plan Free: 100 correos/día (suficiente para pruebas)
```

### 2️⃣ Obtener API Key

```bash
# Después de registro en SendGrid:
# 1. Login: https://app.sendgrid.com
# 2. Menú izquierdo: Settings → API Keys
# 3. Create API Key: Full Access
# 4. Copiar la clave generada (aparece UNA SOLA VEZ)
#    Ejemplo: SG.Xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
# 5. Guardarla de forma segura
```

### 3️⃣ Configurar en .env.local

```bash
# .env.local (ya existe)
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USER=apikey
SMTP_PASS=SG.xxxxxxxxxxxxxxxxxxxxxxxxxxxxxx  # Tu API Key
SMTP_SECURE=true
SMTP_FROM=sistema@getupsoft.com.do
SMTP_FROM_NAME=DGII Certificación
```

### 4️⃣ Prueba Rápida

```bash
# Ejecutar este script:
python -c "
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv

load_dotenv('.env.local')

host = os.getenv('SMTP_HOST')
port = int(os.getenv('SMTP_PORT'))
user = os.getenv('SMTP_USER')
passwd = os.getenv('SMTP_PASS')

try:
    server = smtplib.SMTP(host, port)
    server.starttls()
    server.login(user, passwd)
    
    msg = MIMEMultipart()
    msg['From'] = 'sistema@getupsoft.com.do'
    msg['To'] = 'joelstalin210@gmail.com'
    msg['Subject'] = 'Prueba SendGrid - DGII'
    
    html = '<h2>Correo desde SendGrid ✓</h2><p>Funciona correctamente</p>'
    msg.attach(MIMEText(html, 'html'))
    
    server.sendmail('sistema@getupsoft.com.do', 'joelstalin210@gmail.com', msg.as_string())
    server.quit()
    
    print('✓ Correo enviado a Gmail exitosamente')
except Exception as e:
    print(f'✗ Error: {e}')
"
```

---

## Alternativa Rápida: Gmail SMTP

Si prefieres usar tu cuenta Gmail directamente:

```bash
# .env.local
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=joelstalin210@gmail.com
SMTP_PASS=xxxx-xxxx-xxxx-xxxx  # Contraseña de aplicación (no tu contraseña normal)
SMTP_SECURE=true
```

**Obtener contraseña de aplicación Gmail:**
1. Gmail: Seguridad → Contraseñas de aplicación
2. Seleccionar: Mail + Windows Computer
3. Copiar contraseña de 16 caracteres
4. Usar en SMTP_PASS

---

## Flujo Actual

```
┌─────────────────┐
│  Tu Aplicación  │
└────────┬────────┘
         │ SMTP
         │ (host, port, auth)
         ▼
    SendGrid
    smtp.sendgrid.net:587
         │ (reenvia)
         ▼
    Gmail (joelstalin210@gmail.com)
    📬 RECIBIDO
```

---

## Próximos Pasos

1. **Hoy**: Crear cuenta SendGrid (2 min)
2. **Hoy**: Configurar .env.local (1 min)
3. **Hoy**: Ejecutar prueba (1 min)
4. **Verificar**: Revisar Gmail en joelstalin210@gmail.com

**Después**: Todos los correos de certificación DGII irán al Gmail real.
