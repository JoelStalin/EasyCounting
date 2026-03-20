# 🚀 Mailcow - Sistema de Correos Profesional Integrado

**Mailcow** es una solución self-hosted completa para correos electrónicos. Es mucho mejor que SendGrid o Mailpit para DGII porque:

## ✨ Ventajas de Mailcow

| Aspecto | Mailcow | SendGrid | Mailpit |
|--------|---------|---------|---------|
| **Costo** | 🆓 Gratis | Pago | 🆓 Gratis |
| **Tipo** | Self-Hosted | Cloud/API | Local Demo |
| **SMTP/IMAP** | ✅ Completo | ✅ SMTP Solo | ✅ Solo SMTP |
| **Webmail** | ✅ Sí | ❌ No | ❌ No |
| **Administración** | ✅ Web UI | ✅ Limitada | ❌ No |
| **Dominio Propio** | ✅ Sí | ✅ Requiere Config | ❌ No |
| **Escalable** | ✅ Sí | ✅ Sí | ❌ Solo Local |
| **Certificados SSL** | ✅ Automático | ✅ Sí | ❌ No |
| **Para Producción** | ✅ Sí | ✅ Sí | ❌ No |
| **Profesional** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ |

---

## 🏗️ Arquitectura Mailcow en Docker

```
┌──────────────────────────────────────────────────────┐
│              Docker Compose (Tu Máquina)             │
├──────────────────────────────────────────────────────┤
│                                                      │
│  ┌────────────────┐  ┌─────────────────────────┐   │
│  │  Tu FastAPI    │  │     MAILCOW STACK       │   │
│  │  DGII e-CF     │  │  ┌──────────────────┐   │   │
│  └────────┬────────┘  │  │ Postfix (SMTP)   │   │   │
│           │           │  │ :25, :465, :587  │   │   │
│           │ SMTP      │  ├──────────────────┤   │   │
│           │ :587      │  │ Dovecot (IMAP)   │   │   │
│           └──────────→│  │ :143, :993       │   │   │
│                       │  ├──────────────────┤   │   │
│                       │  │ Webmail (SOGo)   │   │   │
│                       │  │ http://localhost │   │   │
│                       │  ├──────────────────┤   │   │
│                       │  │ Admin (Netdata)  │   │   │
│                       │  │ http://localhost │   │   │
│                       │  ├──────────────────┤   │   │
│                       │  │ MySQL (Base Datos)   │   │
│                       │  │ Redis (Cache)    │   │   │
│                       │  └──────────────────┘   │   │
│                       │                         │   │
│                       └─────────────────────────┘   │
│                                                      │
└──────────────────────────────────────────────────────┘
        ↓ (Correos Internos)
    getupsoft.com.do
```

---

## 🚀 Instalación Rápida (10 minutos)

### Opción A: Mailcow Automático (Recomendado)

```bash
# 1. Clone Mailcow repository
cd c:\Users\yoeli\Documents\dgii_encf
git clone https://github.com/mailcow/mailcow-dockerized mailcow

# 2. Generate config
cd mailcow
bash generate_config.sh

# 3. Responder preguntas:
#    - Hostname: mail.getupsoft.com.do (o tu dominio)
#    - Timezone: America/Santo_Domingo (UTC-4)

# 4. Start Mailcow
docker-compose up -d

# 5. Esperar 2-3 minutos para que todo levante
docker-compose ps

# 6. Acceder a administración
# https://localhost (con certificado auto-firmado)
# user: admin
# password: moohoo (default - CAMBIAR)
```

### Opción B: Mailcow en docker-compose.yml Actual

Agregaremos Mailcow al docker-compose.yml existente.

---

## 📊 Configuración Post-Instalación

### 1. Crear Usuario/Dominio en Mailcow

```bash
# Acceder a: https://localhost/admin
# Menú: Mail Accounts → Add Mailbox

# Datos:
Domain: getupsoft.com.do
Mailbox: sistema@getupsoft.com.do
Password: [Tu contraseña segura]
```

### 2. Configurar en .env.local

```bash
# .env.local
# Mailcow Configuration
MAILCOW_ENABLED=true
SMTP_HOST=mailcow-postfix  # O localhost si está en otro host
SMTP_PORT=587              # TLS
SMTP_USER=sistema@getupsoft.com.do
SMTP_PASS=tu_contraseña_mailcow
SMTP_FROM=sistema@getupsoft.com.do
SMTP_SECURE=true

# Alternativas (si quieres SMTP simple sin TLS)
# SMTP_PORT=25 (sin autenticación - solo local network)
# SMTP_PORT=465 (SMTPS - SSL obligatorio)
```

### 3. Prueba Rápida

```python
import smtplib
from email.mime.text import MIMEText

server = smtplib.SMTP('localhost', 587)
server.starttls()
server.login('sistema@getupsoft.com.do', 'tu_contraseña')

msg = MIMEText('Prueba desde Mailcow')
msg['Subject'] = 'Test Mailcow'
msg['From'] = 'sistema@getupsoft.com.do'
msg['To'] = 'joelstalin210@gmail.com'

server.sendmail('sistema@getupsoft.com.do', 'joelstalin210@gmail.com', msg.as_string())
server.quit()

print("✓ Correo enviado desde Mailcow")
```

---

## 🌐 Acceso Mailcow Web

| Función | URL | Usuario |
|---------|-----|---------|
| **Admin Panel** | https://localhost | admin |
| **Webmail** | https://localhost/mail | tu@email.com |
| **API** | https://localhost/api | admin |
| **Documentación** | https://mailcow.github.io | - |

---

## 📧 Características Completas

✅ **SMTP** - Envío de correos  
✅ **IMAP** - Recepción de correos  
✅ **Webmail** - Cliente web (SOGo)  
✅ **Antispam** - Rspamd integrado  
✅ **Antivirus** - ClamAV integrado  
✅ **SSL/TLS** - Certificados automáticos  
✅ **Backups** - Sistema automático  
✅ **Monitoreo** - Netdata integrado  
✅ **API** - Para automatización  
✅ **Logs** - Auditoria completa  

---

## 🔧 Ventajas para DGII

1. **Sistema Profesional**: Todo integrado, no requiere externes
2. **Correos Reales**: getupsoft.com.do@sistema (con dominio propio)
3. **Webmail Incluido**: Ver correos sin cliente externo
4. **Logs Auditables**: Para certificación DGII
5. **Escalable**: Puedes tener más usuarios/dominios
6. **Gratuito**: Sin costos mensuales
7. **Self-Hosted**: Datos bajo tu control
8. **SPF/DKIM/DMARC**: Configurables fácilmente

---

## ⚡ Migración desde SendGrid/Mailpit

```bash
# YA TIENES:
# ✓ Mailpit (local, solo demostración) → REEMPLAZAR
# ✓ SendGrid (externo) → OPCIONAL mantener como backup

# CAMBIO:
# Todos los correos: FastAPI → Mailcow :587
# SMTP_HOST cambia de "mailpit" a "mailcow-postfix"
```

---

## 📝 Next Steps

1. ✅ Clonar Mailcow
2. ✅ Generar config
3. ✅ Levantarlo en Docker
4. ✅ Crear usuario sistema@getupsoft.com.do
5. ✅ Actualizar .env.local
6. ✅ Probar SMTP
7. ✅ Enviar correo de DGII a joelstalin210@gmail.com
8. ✅ Verificar en Webmail de Mailcow

---

**Mailcow es la solución profesional que merece tu certificación DGII** 🚀
