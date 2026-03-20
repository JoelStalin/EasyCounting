# Plan de Ejecución: Certificación Completa DGII e-CF

**Fecha**: 20 de Marzo de 2026  
**Usuario**: JOEL STALIN  
**RNC**: 25500706423  
**Email de Prueba**: joelstalin210@gmail.com  
**Rama**: refactor/auditoria  
**Estado**: En Progreso

---

## 🔴 FASE 1: REMEDIACIÓN CRÍTICA DE SEGURIDAD

### 1.1 Credenciales Expuestas en Repositorio

**Problema**: Archivo `scripts/automation/assist_cloudflare_login.py` contiene credenciales hardcodeadas.

**Acción Inmediata**:

```powershell
# 1. CAMBIAR contraseña Cloudflare
# - Abre: https://dash.cloudflare.com/
# - Login con Joelstalin2105@gmail.com
# - Account Settings → Authentication → Change Password
# - NUEVA CONTRASEÑA: Genera una fuerte con mayúsculas, números, símbolos
# - Guarda en gestor de contraseñas (1Password, LastPass, etc)
```

**Acción de Código**:

```powershell
# Limpiar credenciales del repositorio
cd c:\Users\yoeli\Documents\dgii_encf

# Generar API Token en lugar de user/pass
# https://dash.cloudflare.com/profile/api-tokens
# Token Permissions:
# - Zone.Zone:Read
# - Zone.DNS:Edit
# Recursos: Específico a getupsoft.com.do

# Guardar el token en un archivo seguro local (no versionar):
# Windows Credentials Manager o archivo .env.local apartado
```

**Limpiar archivo de código**:

```bash
# Esto se hará sin exponer credenciales
# Ver sección "Correcciones de Seguridad" al final de este documento
```

---

## 🟡 FASE 2: CONFIGURACIÓN DE REGISTROS MX EN CLOUDFLARE

### 2.1 Requisitos

- ✅ Token API de Cloudflare (generado en Fase 1)
- ✅ Acceso a dash.cloudflare.com con perfil JOEL STALIN
- ✅ Servidor SMTP configurado (local o SES)
- ✅ Dominio: `getupsoft.com.do` (o confirmado)

### 2.2 Pasos Manuales en Cloudflare UI

```markdown
1. Abre: https://dash.cloudflare.com/
2. Selecciona dominio: getupsoft.com.do
3. DNS → Records → Add record

MX Records a Agregar:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Tipo    | Nombre          | Contenido              | Prioridad | TTL
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
MX      | @               | mail.getupsoft.com.do  | 10        | Auto
MX      | @               | mail2.getupsoft.com.do | 20        | Auto
TXT     | @               | v=spf1 include:... ~all| -         | Auto
CNAME   | mail._domainkey | dkim-record.provider   | -         | Auto
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

a. Crear registro MX primario:
   - Type: MX
   - Name: @ (ejemplo: getupsoft.com.do)
   - Mail server: mail.getupsoft.com.do
   - Priority: 10
   - Proxy: Gray cloud (DNS only)
   - TTL: Auto
   - [Save]

b. Crear registro MX secundario (backup):
   - Type: MX
   - Name: @ (mismo)
   - Mail server: mail2.getupsoft.com.do
   - Priority: 20
   - TTL: Auto
   - [Save]

c. Crear SPF record (prevenir spoofing):
   - Type: TXT
   - Name: @ 
   - Content: v=spf1 include:sendgrid.net ~all
     (ajustar si usas otro proveedor SMTP)
   - [Save]

d. Crear DKIM record (firmar correos):
   - (Obtener de tu proveedor SMTP: SendGrid, AWS SES, etc)
   - Type: CNAME o TXT
   - [Save]

4. Esperar propagación DNS (5-10 minutos)
5. Verificar: dig mx getupsoft.com.do @8.8.8.8
```

### 2.3 Verificación de Registros MX

```powershell
# En PowerShell:
nslookup -type=MX getupsoft.com.do 8.8.8.8

# Salida esperada:
# Non-authoritative answer:
# getupsoft.com.do   MX preference = 10, mail exchanger = mail.getupsoft.com.do
# getupsoft.com.do   MX preference = 20, mail exchanger = mail2.getupsoft.com.do
```

---

## 🟡 FASE 3: CONFIGURACIÓN SMTP LOCAL

### 3.1 Obtener Credenciales SMTP

**Opción A: SendGrid (recomendado)**
```
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USER=apikey
SMTP_PASS=SG.xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
SMTP_FROM=noreply@getupsoft.com.do
```

**Opción B: AWS SES**
```
SMTP_HOST=email-smtp.us-east-1.amazonaws.com
SMTP_PORT=587
SMTP_USER=AKIAIOSFODNN7EXAMPLE
SMTP_PASS=BPM...largacontraseña...
SMTP_FROM=no-reply@getupsoft.com.do
```

**Opción C: Mailtrap (pruebas)**
```
SMTP_HOST=live.smtp.mailtrap.io
SMTP_PORT=587
SMTP_USER=your_mailtrap_user
SMTP_PASS=your_mailtrap_password
SMTP_FROM=hello@example.com
```

### 3.2 Configurar `.env.local`

```bash
cd c:\Users\yoeli\Documents\dgii_encf

# Copiar template
cp .env.example .env.local

# Editar con valores SMTP reales (NO versionar):
```

**Contenido `.env.local` (ejemplo con SendGrid)**:

```bash
# === SMTP para Email Transaccional ===
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USER=apikey
SMTP_PASS=SG.YOUR_SENDGRID_API_KEY_HERE  # ⚠️ NO PUSHEADO A GIT
SMTP_SECURE=true
SMTP_FROM=noreply@getupsoft.com.do
SMTP_TIMEOUT_SECONDS=20

# === Verificación SMTP ===
# Prueba: python scripts/automation/send_test_email.py \
#   --to=joelstalin210@gmail.com \
#   --subject="Prueba MX - 20 Marzo 2026" \
#   --text="Correo de validacion MX records en Cloudflare"
```

---

## 🟢 FASE 4: PRUEBA DE ENVÍO DE EMAIL

### 4.1 Preparar Ambiente

```powershell
# Terminal PowerShell en c:\Users\yoeli\Documents\dgii_encf

# 1. Verificar Python
python --version
# Esperado: Python 3.12.x

# 2. Instalar dependencias si falta poetry
pip install poetry

# 3. Instalar deps del proyecto
poetry install --sync
```

### 4.2 Enviar Correo de Prueba

```powershell
# Método 1: Script Python directo
$env:FLASK_ENV = "development"

poetry run python scripts/automation/send_test_email.py `
  --to=joelstalin210@gmail.com `
  --subject="Test MX Records - DGII Certificación 20 Marzo 2026" `
  --text="Este es un correo de prueba para validar MX records en Cloudflare." `
  --html="<h2>Test MX Records</h2><p>Si recibes este correo, los MX están correctos.</p>"
```

### 4.3 Verificar Entrega

**1. Revisar Bandeja de JOEL STALIN**

```
Gmail: joelstalin210@gmail.com
- Esperar 30-60 segundos
- Revisar: Inbox, Spam, Promotions
- Verificar remitente: noreply@getupsoft.com.do
```

**2. Revisar Logs de la Aplicación**

```powershell
# Si el backend está corriendo localmente:
docker logs dgii_encf-web-1 | grep -i "email\|smtp\|mail"

# O revisar con Make:
make logs
```

**3. Revisar en Proveedor SMTP**

**SendGrid**:
```
https://app.sendgrid.com/
→ Mail Activity
→ Buscar: joelstalin210@gmail.com
→ Ver estado: Delivered, Bounced, etc.
```

**AWS SES**:
```
AWS Console → SES → Sent emails
Filtrar por recipient: joelstalin210@gmail.com
Ver status: Sent, Delivered, Bounced, etc.
```

### 4.4 Validación Exitosa ✅

```
✓ Correo recibido en joelstalin210@gmail.com
✓ Remitente: noreply@getupsoft.com.do
✓ Asunto: "Test MX Records - DGII Certificación..."
✓ HTML renderizado correctamente
✓ Sin marca de SPAM
✓ Logs sin errores
```

**Si hay problemas**: Ver sección "Troubleshooting" al final.

---

## 🔵 FASE 5: PREPARACIÓN CERTIFICACIÓN DGII

### 5.1 Estructura de Certificación DGII

El proceso tiene **15 pasos** (según documentación oficial):

```
┌─ Paso 1: Registrado ✅ (ya completado en el portal DGII)
├─ Paso 2: Pruebas de Datos e-CF
├─ Paso 3: Pruebas de Datos Aprobación Comercial
├─ Paso 4: Pruebas Simulación e-CF
├─ Paso 5: Pruebas Simulación Representación Empresa
├─ Paso 6: Validación Representación Empresa
├─ Paso 7: URL Servicios Prueba
├─ Paso 8: Inicio Prueba Recepción e-CF
├─ Paso 9: Recepción e-CF
├─ Paso 10: Inicio Prueba Recepción Aprobación Comercial
├─ Paso 11: Recepción Aprobación Comercial
├─ Paso 12: URL Servicios Producción
├─ Paso 13: Declaración Jurídica
├─ Paso 14: Verificación Estatus
└─ Paso 15: Finalizado
```

RNC de JOEL STALIN: `25500706423`

### 5.2 Revisar Status Actual en DGII

```bash
# Opción 1: Via Portal OFV (manual, interactive)
# https://dgii.gov.do/OFV/home.aspx
# Login: RNC 25500706423

# Opción 2: Via script Python (automatizado)
cd c:\Users\yoeli\Documents\dgii_encf

poetry run python3 << 'EOF'
import asyncio
from app.services.dgii_scraper.certification_bot import DGIICertificationBot

async def main():
    bot = DGIICertificationBot(
        rnc="25500706423",
        password="TU_CONTRASEÑA_DGII"  # Obtener de forma segura
    )
    status = await bot.check_certification_status()
    print("Estado actual de certificación:")
    print(f"  RNC: {status['rnc']}")
    print(f"  Estado: {status['certification_state']}")
    print(f"  Paso: {status['step']}")
    print(f"  Mensaje: {status['message']}")

asyncio.run(main())
EOF
```

### 5.3 Preparar Certificados Digitales

```bash
# 1. Obtener certificado .p12 de DGII
# - Portal OFV → Descargar Certificado Digital
# - Guardar en: c:\Users\yoeli\Documents\dgii_encf\secrets\cert.p12

# 2. Configurar en .env.local
DGII_CERT_P12_PATH=/secrets/cert.p12
DGII_CERT_P12_PASSWORD=TU_CONTRASEÑA_P12

# 3. Validar certificado
poetry run python3 << 'EOF'
from pathlib import Path
from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography.hazmat.backends import default_backend

cert_path = Path("/secrets/cert.p12")
password = b"TU_CONTRASEÑA_P12"

try:
    with open(cert_path, "rb") as f:
        private_key, certificate, ca_certs = pkcs12.load_key_and_certificates(
            f.read(), password, backend=default_backend()
        )
    print("✓ Certificado válido")
    print(f"  Emisor: {certificate.issuer}")
    print(f"  Vencimiento: {certificate.not_valid_after}")
except Exception as e:
    print(f"✗ Error: {e}")
EOF
```

---

## 🟣 FASE 6: EJECUTAR SUITE DE CERTIFICACIÓN

### 6.1 Ambiente Pre-Certificación (PRECERT)

```bash
cd c:\Users\yoeli\Documents\dgii_encf

# Levantar stack local
make up

# Esperar ~30 segundos a que PostgreSQL e Redis estén listos
# Migrar BD
make migrate

# Verificar salud
curl -s http://localhost:8080/readyz | jq
# Esperado: {"status":"ready","database":"connected","redis":"connected"}
```

### 6.2 Ejecutar Batería de Pruebas PRECERT

```powershell
# Script de pruebas (ya existe en el repo)
cd c:\Users\yoeli\Documents\dgii_encf

# Ejecutar tests de DGII
poetry run pytest app/tests/test_dgii_client.py -v

# O ejecutar suite completa
make test
```

### 6.3 Enviar Set de Pruebas a DGII

```bash
# El set incluye:
# ✓ e-CF 31 (Crédito Fiscal - B2B)
# ✓ e-CF 32 (Consumo - B2C)
# ✓ e-CF 33 (Nota de Crédito)
# ✓ e-CF 34 (Nota de Débito)
# ✓ ARECF (Acuse de Recibo)
# ✓ ACECF (Aprobación Comercial)
# ✓ ANECF (Anulación de e-NCF)

# Cargar en portal OFV:
# 1. Loguear en: https://dgii.gov.do/OFV
# 2. RNC: 25500706423
# 3. Paso 2 → Cargar archivo XML del set
# 4. Esperar validación DGII (24-48 horas)
```

### 6.4 Verificar Respuestas DGII

```bash
# Revisar trackIds y estados
curl -s -H "Authorization: Bearer <TOKEN_DGII>" \
  "https://ecf.dgii.gov.do/TesteCF/consultatrackids?rnc=25500706423" \
  | jq

# Guardar evidencia en: docs/_pruebas/respuestas_precert_2026-03-20.json
```

---

## 🟣 FASE 7: MIGRAR A CERTIFICACIÓN (CERT)

### 7.1 Cambiar Variables de Ambiente

```bash
# .env.local
# Cambiar:
DGII_ENV=CERT  # Era: PRECERT

DGII_AUTH_BASE_URL=https://ecf.dgii.gov.do/CerteCF/Autenticacion
DGII_RECEPCION_BASE_URL=https://ecf.dgii.gov.do/CerteCF/Recepcion
DGII_CONSULTA_RESULTADO_BASE_URL=https://ecf.dgii.gov.do/CerteCF/ConsultaResultado
```

### 7.2 Ejecutar Pruebas CERT

```bash
# Repetir suite de pruebas en ambiente CERT
poetry run pytest app/tests/test_dgii_client.py::test_ecf_certification -v

# Guardar evidencia:
# - XML firmados
# - trackIds
# - Respuestas DGII
# - Logs de aplicación
```

---

## 📊 FASE 8: DOCUMENTAR EVIDENCIA

### 8.1 Estructura de Evidencia

```
docs/_pruebas/
├── 2026-03-20_precert_set.xml          # Set de pruebas enviado
├── 2026-03-20_precert_response.json    # Respuesta DGII
├── trackIds_precert.txt                # Track IDs
├── 2026-03-20_cert_set.xml
├── 2026-03-20_cert_response.json
├── trackIds_cert.txt
├── screenshots_ofv/                    # Capturas del portal OFV
│   ├── paso_1_registrado.png
│   ├── paso_2_pruebas_datos.png
│   ├── step_15_finalizado.png
└── logs/
    ├── app_logs_2026-03-20.log
    ├── smtp_test_log.txt
    └── dgii_api_calls.log
```

### 8.2 Checklist de Evidencia a Guardar

```markdown
📋 Evidencia SMTP/MX:
  ☐ Screenshot: MX records en Cloudflare
  ☐ Output: nslookup -type=MX getupsoft.com.do
  ☐ Screenshot: Correo recibido en joelstalin210@gmail.com
  ☐ Log: send_test_email.py output
  ☐ Log: SMTP connection successful

📋 Evidencia Certificación:
  ☐ archivo .p12 validado (certificado digital)
  ☐ XML e-CF 31 (Crédito B2B) - firmado
  ☐ QR código en Representación Impresa
  ☐ respuesta DGII con trackId
  ☐ Paso final "Finalizado" en portal OFV
  ☐ Logs sin errores
  ☐ Audit trail en app/models/audit
```

---

## 🔴 TROUBLESHOOTING

### Email no llega / SMTP Error

**Síntoma**: `SMTPAuthenticationError: 535 Invalid credentials`

```bash
# 1. Verificar credenciales SMTP
echo $env:SMTP_USER
echo $env:SMTP_PASS

# 2. Testear conexión manual
python3 << 'EOF'
import smtplib
host = "smtp.sendgrid.net"
port = 587
user = "apikey"
password = "SG.YOUR_KEY"

try:
    server = smtplib.SMTP(host, port)
    server.starttls()
    server.login(user, password)
    print("✓ SMTP Connection OK")
    server.quit()
except smtplib.SMTPAuthenticationError as e:
    print(f"✗ Auth Error: {e}")
except Exception as e:
    print(f"✗ Error: {e}")
EOF

# 3. Revisar logs del proveedor SMTP
# SendGrid: https://app.sendgrid.com/mail_activity
# AWS SES: AWS Console → CloudWatch Logs
```

### MX Records no se propagan

**Síntoma**: `nslookup -type=MX getupsoft.com.do` retorna sin resultados

```bash
# 1. Forzar refresh DNS
ipconfig /flushdns

# 2. Esperar 5-10 minutos más (TTL puede ser hasta 3600 segundos)

# 3. Verificar con otros nameservers
nslookup -type=MX getupsoft.com.do 1.1.1.1    # Cloudflare
nslookup -type=MX getupsoft.com.do 8.8.8.8    # Google

# 4. Si aún falla: Revisar Cloudflare que MX fue guardado
# dashboard.cloudflare.com → DNS → Buscar MX
```

### Certificado .p12 inválido

**Síntoma**: `Failed to load certificate from p12: invalid password`

```bash
# 1. Verificar archivo existe
ls -la /secrets/cert.p12

# 2. Testear contraseña
openssl pkcs12 -info -in /secrets/cert.p12 -passin pass:TU_PASSWORD

# 3. Si contraseña es incorrecta: Descargar nuevamente desde DGII OFV
```

### DGII Portal inaccesible

**Síntoma**: `Connection timeout a ecf.dgii.gov.do`

```bash
# 1. Verificar conectividad
ping ecf.dgii.gov.do

# 2. Revisar firewall/proxy corporativo
curl -I https://ecf.dgii.gov.do/TesteCF/Autenticacion -v

# 3. Si es intermitente: Implementar circuit breaker
# (ya incluido en app/dgii/client.py)
```

---

## ✅ CHECKLIST FINAL

```
FASE 1 - SEGURIDAD:
  ☐ Contraseña Cloudflare rotada
  ☐ API Token generado y guardado seguro
  ☐ Credenciales removidas del código
  ☐ .env.local agregado a .gitignore

FASE 2 - REGISTROS MX:
  ☐ MX registros creados en Cloudflare
  ☐ SPF record configurado
  ☐ DKIM record agregado
  ☐ DNS propagado (nslookup verifica)

FASE 3 - SMTP:
  ☐ Credenciales SMTP obtenidas
  ☐ .env.local configurado
  ☐ Conexión SMTP validada

FASE 4 - EMAIL:
  ☐ Correo de prueba enviado
  ☐ Recibido en joelstalin210@gmail.com
  ☐ Verificado en bandeja (no spam)
  ☐ Logs sin errores

FASE 5-8 - CERTIFICACIÓN DGII:
  ☐ Status PRECERT verificado (Paso 1)
  ☐ Set de pruebas generado
  ☐ Set enviado a DGII
  ☐ Respuesta DGII documentada
  ☐ Migración a CERT realizada
  ☐ Pruebas CERT completadas
  ☐ Evidencia compilada
  ☐ Portal OFV: Paso 15 "Finalizado"

DOCUMENTACIÓN:
  ☐ Archivo este: PLAN_EJECUCION completado
  ☐ Evidencia guardada en docs/_pruebas/
  ☐ Logs archivados
  ☐ Screenshots capturados
```

---

## 📞 CONTACTOS DE SOPORTE DGII

```
Portal OFV:        https://dgii.gov.do/OFV
Email Soporte:     participantes@dgii.gov.do
Teléfono:          +1(809) 555-2727 ext. 2XXX
Ambiente PRECERT:  https://ecf.dgii.gov.do/TesteCF
Ambiente CERT:     https://ecf.dgii.gov.do/CerteCF
Ambiente PROD:     https://ecf.dgii.gov.do/ecf
```

---

## 📚 REFERENCIAS

- [Descripción Técnica e-CF](docs/oficial/_evidencia)
- [Guía de Implementación](docs/DGII-Guia-Implementacion.md)
- [Checklist Certificación](docs/guide/06-certificacion-checklist.md)
- [Runbook Real Certificación](scripts/automation/REAL_CERTIFICATION_RUNBOOK.md)

---

**Última actualización**: 20 de Marzo de 2026 - 14:45 AST

*Plan preparado por: GitHub Copilot para proyecto DGII e-CF*
