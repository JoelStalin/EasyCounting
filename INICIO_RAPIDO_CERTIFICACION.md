# 🚀 INICIO RÁPIDO: Certificación DGII + MX Cloudflare

**Estado**: Lista para ejecutar  
**Usuario**: JOEL STALIN  
**RNC**: 25500706423  
**Email de prueba**: joelstalin210@gmail.com  
**Fecha**: 20 de Marzo de 2026  

---

## ⚠️ PASO 0: SEGURIDAD (HACER PRIMERO)

### 0.1 Cambiar Contraseña Cloudflare

Tu contraseña de Cloudflare fue encontrada en el repositorio. **DEBE ser cambiada hoy**:

```powershell
# 1. Abre en tu navegador (perfil JOEL STALIN):
# https://dash.cloudflare.com/

# 2. Login: Joelstalin2105@gmail.com
# 3. Ir a: Settings (esquina abajo izquierda)
# 4. Account → Authentication → Change Password
# 5. Nueva contraseña FUERTE (16+ caracteres)
# 6. Guardar en tu gestor de credenciales
```

✓ **Completado**: Documento [REMEDIACION_SEGURIDAD_CREDENCIALES_EXPUESTAS.md](docs/REMEDIACION_SEGURIDAD_CREDENCIALES_EXPUESTAS.md)

### 0.2 Generar API Token Cloudflare

```powershell
# 1. Abre: https://dash.cloudflare.com/profile/api-tokens
# 2. "Create Token"
# 3. Permisos:
#    ☑ Zone.Zone:Read
#    ☑ Zone.DNS:Edit
# 4. Recursos: Specific zone → getupsoft.com.do
# 5. Copiar token generado
# 6. Guardar en variable de entorno:

$env:CLOUDFLARE_API_TOKEN = "tu-token-aqui-40-caracteres"

# 7. Verificar:
echo $env:CLOUDFLARE_API_TOKEN
```

---

## 📋 PASO 1-5: CONFIGURAR MX + EMAIL

Documento completo: [PLAN_EJECUCION_CERTIFICACION_COMPLETA.md](docs/PLAN_EJECUCION_CERTIFICACION_COMPLETA.md)

### 1.1 Configurar MX Records en Cloudflare (AUTOMATIZADO)

```powershell
cd c:\Users\yoeli\Documents\dgii_encf

# Asegurar que tengas el token en env var:
$env:CLOUDFLARE_API_TOKEN = "tu-token-aqui"

# Ejecutar script seguro:
poetry run python scripts/automation/setup_cloudflare_mx_safe.py `
  --domain getupsoft.com.do `
  --mx-host mail.getupsoft.com.do `
  --mx-priority 10 `
  --output artifacts_live_dns/mx_records_created.json

# Esperado:
# ✅ Zone ID obtenido
# ✅ MX Record creado
# ✅ SPF Record creado
# ✅ JSON guardado
```

### 1.2 Verificar MX Records (DNS Propagation)

```powershell
# Esperar 5-10 minutos, luego:
nslookup -type=MX getupsoft.com.do 8.8.8.8

# Esperado:
# Non-authoritative answer:
# getupsoft.com.do   MX preference = 10, mail exchanger = mail.getupsoft.com.do
```

### 1.3 Configurar SMTP en `.env.local`

```bash
cp .env.example .env.local

# Editar .env.local y añadir:
SMTP_HOST=smtp.sendgrid.net           # O tu proveedor
SMTP_PORT=587
SMTP_USER=apikey
SMTP_PASS=SG.YOUR_API_KEY_HERE        # ⚠️ USA VARIABLE DE ENTORNO
SMTP_FROM=noreply@getupsoft.com.do
SMTP_TIMEOUT_SECONDS=20

# NO VERSIONAR .env.local en git
```

**Proveedores recomendados**:
- SendGrid: `smtp.sendgrid.net` → Obtén key en https://app.sendgrid.com/settings/api_keys
- AWS SES: `email-smtp.us-east-1.amazonaws.com` 
- Mailtrap (pruebas): `live.smtp.mailtrap.io`

### 1.4 Enviar Email de Prueba

```powershell
cd c:\Users\yoeli\Documents\dgii_encf

# Asegurar que tengas .env.local con SMTP configurado
# Luego:

poetry run python scripts/automation/send_test_email.py `
  --to=joelstalin210@gmail.com `
  --subject="Test MX - 20 Marzo 2026" `
  --text="Correo de prueba desde GetUpSoft"

# Verificar:
# 1. Abre Gmail: joelstalin210@gmail.com
# 2. Debería llegar en Inbox (no Spam)
# 3. Remitente: noreply@getupsoft.com.do
```

---

## 🔷 PASO 6-8: CERTIFICACIÓN DGII

### 6.1 Levantar Stack Local

```powershell
cd c:\Users\yoeli\Documents\dgii_encf

# Levantar Docker Compose
make up

# Esperar ~30 segundos
# Verificar salud:
curl http://localhost:8080/readyz

# Esperado: {"status":"ready","database":"connected","redis":"connected"}

# Ver logs:
make logs
```

### 6.2 Revisar Status de Certificación DGII

```powershell
# Portal OFV (manual):
# https://dgii.gov.do/OFV
# Login: RNC 25500706423
# Buscar: Paso actual (debería ser Paso 1: Registrado o mayor)
```

### 6.3 Generar Set de Pruebas

```powershell
# Los scripts e-CF están listos en:
# app/services/dgii_scraper/certification_bot.py
# labs/odoo15_testing_env/dgii_test_set_runner.py

# Ejecutar tests:
make test

# O específico:
poetry run pytest app/tests/test_dgii_client.py::test_ecf_certification -v
```

### 6.4 Cargar Set en Portal OFV

```
1. Abre: https://dgii.gov.do/OFV
2. Login con RNC: 25500706423
3. Ir a: Paso 2 - Pruebas de Datos
4. Cargar archivo XML del set de pruebas
5. DGII responde en 24-48 horas
```

### 6.5 Guardar Evidencia

```powershell
# Crear carpeta:
mkdir docs/_pruebas/2026-03-20

# Guardar:
# 1. XML sets (firmados)
# 2. trackIds de respuesta
# 3. Screenshots del portal OFV
# 4. Logs de aplicación
# 5. JSON de respuestas DGII

# Ver documentación completa:
docs/PLAN_EJECUCION_CERTIFICACION_COMPLETA.md (sección "Documentar Evidencia")
```

---

## ✅ CHECKLIST RÁPIDO

```
SEGURIDAD:
  ☐ Contraseña Cloudflare cambiada (Joelstalin2105@gmail.com)
  ☐ API Token generado y en $env:CLOUDFLARE_API_TOKEN

MX + EMAIL:
  ☐ MX Records creados (setup_cloudflare_mx_safe.py)
  ☐ DNS propagado (nslookup verifica)
  ☐ SMTP configurado en .env.local
  ☐ Email de prueba enviado y recibido

DGII CERTIFICACIÓN:
  ☐ Stack Docker levantado (make up)
  ☐ Salud verificada (/readyz)
  ☐ Status actual revisado (OFV Portal)
  ☐ Suite de pruebas generada
  ☐ Set de pruebas cargado en DGII
  ☐ Evidencia guardada en docs/_pruebas/
```

---

## 📞 PRÓXIMOS PASOS

1. **Ahora**: Cambiar contraseña Cloudflare + generar API Token
2. **5 min**: Crear MX records con script seguro
3. **10 min**: Enviar email de prueba
4. **30 min**: Levantar stack Docker y revisar DGII OFV
5. **1-2 días**: Esperar respuesta DGII del set de pruebas
6. **Final**: Compilar evidencia y solicitar aprobación

---

## 📚 ARCHIVOS CLAVE

- **Plan Completo**: [PLAN_EJECUCION_CERTIFICACION_COMPLETA.md](docs/PLAN_EJECUCION_CERTIFICACION_COMPLETA.md)
- **Seguridad**: [REMEDIACION_SEGURIDAD_CREDENCIALES_EXPUESTAS.md](docs/REMEDIACION_SEGURIDAD_CREDENCIALES_EXPUESTAS.md)
- **Runbook Real**: [scripts/automation/REAL_CERTIFICATION_RUNBOOK.md](scripts/automation/REAL_CERTIFICATION_RUNBOOK.md)
- **Guía Técnica**: [docs/DGII-Guia-Implementacion.md](docs/DGII-Guia-Implementacion.md)

---

## 🆘 PROBLEMAS?

Ver sección "TROUBLESHOOTING" en:  
[PLAN_EJECUCION_CERTIFICACION_COMPLETA.md](docs/PLAN_EJECUCION_CERTIFICACION_COMPLETA.md#-troubleshooting)

---

**¿Listo para comenzar?** 👉 [PASO 0: Seguridad ⬆️](#-paso-0-seguridad-hacer-primero)

Última actualización: 2026-03-20 15:00 AST
