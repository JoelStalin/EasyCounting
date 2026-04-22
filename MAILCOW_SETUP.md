# 🚀 Mailcow - Sistema de Correos Profesional Integrado

**Mailcow** es la ruta de produccion recomendada para `mail.getupsoft.com.do`. La automatizacion del repositorio ahora apunta a preparar primero el host remoto por SSH y luego aplicar DNS en Cloudflare sin depender de cambios manuales dentro del repo de la app.

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

## Flujo recomendado para GetUpSoft

### 1. Preparar el host remoto sin tocar servicios existentes

Usa el wrapper PowerShell o el script Python directo. Por defecto prepara Docker + Mailcow en modo seguro, **sin levantar contenedores** y usando puertos web alternos `8081/8443` para no chocar con routers o reverse proxy existentes.

```powershell
.\scripts\automation\prepare_getupsoft_mailcow.ps1 `
  -SshHost getupsoft `
  -Hostname mail.getupsoft.com.do `
  -RemoteDir /opt/mailcow-dockerized `
  -HttpPort 8081 `
  -HttpsPort 8443
```

Salida esperada:
- instala Docker y Compose Plugin si faltan;
- clona o actualiza `mailcow-dockerized` en `/opt/mailcow-dockerized`;
- genera/alinea `mailcow.conf`;
- deja reporte remoto de listeners y posibles conflictos en `/var/tmp/mailcow-getupsoft-preflight.txt`;
- guarda evidencia local en `artifacts_live_dns/getupsoft_mailcow_prepare.log`.

### 2. Aplicar DNS reales en Cloudflare

La automatizacion de DNS usa API token. Selenium queda como apoyo opcional para abrir el dashboard con tu perfil real, pero **no reemplaza** el token.

```powershell
$env:CLOUDFLARE_API_TOKEN="tu-token"

.\scripts\automation\run_real_cloudflare_mail_setup.ps1 `
  -MailIPv4 "IP_PUBLICA_REAL" `
  -EnableAutodiscover
```

Si quieres que tambien abra el navegador para validar visualmente:

```powershell
.\scripts\automation\run_real_cloudflare_mail_setup.ps1 `
  -MailIPv4 "IP_PUBLICA_REAL" `
  -EnableAutodiscover `
  -AssistLogin
```

### 3. Levantar Mailcow cuando puertos y routing esten listos

Una vez confirmados NAT, firewall y puertos publicos, repite el paso remoto con `-StartStack`. Si ya liberarás `80/443` para Mailcow en ese host, cambia esos puertos en la ejecucion:

```powershell
.\scripts\automation\prepare_getupsoft_mailcow.ps1 `
  -SshHost getupsoft `
  -Hostname mail.getupsoft.com.do `
  -HttpPort 80 `
  -HttpsPort 443 `
  -StartStack
```

Si detecta conflictos de puertos, el script aborta antes de levantar los contenedores.

---

## 📊 Configuración Post-Instalación

### 1. Crear Usuario/Dominio en Mailcow

```bash
# Acceder a: https://mail.getupsoft.com.do/admin
# (o https://host:8443/admin mientras estes en modo de preparacion segura)
# Menú: Mail Accounts → Add Mailbox

# Datos:
Domain: getupsoft.com.do
Mailbox: sistema@getupsoft.com.do
Password: [Tu contraseña segura]
```

### 2. Configurar en .env.local

```bash
# .env.local o secretos del entorno productivo
MAILCOW_ENABLED=true
SMTP_HOST=mail.getupsoft.com.do
SMTP_PORT=587
SMTP_USER=noreply@getupsoft.com.do
SMTP_PASS=tu_contraseña_mailcow
SMTP_FROM=noreply@getupsoft.com.do
SMTP_SECURE=true
```

### 3. Prueba Rápida

```python
import smtplib
from email.mime.text import MIMEText

server = smtplib.SMTP('mail.getupsoft.com.do', 587)
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
| **Admin Panel** | https://mail.getupsoft.com.do | admin |
| **Webmail** | https://mail.getupsoft.com.do/SOGo | tu@email.com |
| **API** | https://mail.getupsoft.com.do/api | admin |
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
# SMTP_HOST cambia de "mailpit" o proveedor externo a "mail.getupsoft.com.do"
```

---

## 📝 Next Steps

1. Preparar host remoto con `prepare_getupsoft_mailcow`
2. Aplicar DNS con `run_real_cloudflare_mail_setup.ps1`
3. Publicar DKIM real desde Mailcow
4. Levantar stack cuando puertos esten libres
5. Crear buzones reales (`info`, `ventas`, `soporte`, `noreply`, `admin`)
6. Actualizar secretos SMTP de la app
7. Probar SMTP/IMAP y entregabilidad

---

**Mailcow es la solución profesional que merece tu certificación DGII** 🚀
