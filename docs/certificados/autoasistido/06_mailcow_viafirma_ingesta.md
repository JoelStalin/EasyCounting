# 06 - Ingesta Mailcow para Viafirma (autoasistido)

## Objetivo
Automatizar la recepcion de correos del proceso RA de Viafirma (`ra.viafirma.do`) para avanzar casos de certificado en `certificate-workflow`.

## Alcance de automatizacion
- Si llega correo valido con `case_id` y adjunto `.p12/.pfx`:
  - registra evento `MAIL_INTAKE_EMAIL_RECEIVED`;
  - guarda artefacto en storage seguro;
  - marca estado `CERTIFICATE_RECEIVED`;
  - intenta validar automaticamente si detecta password en el cuerpo;
  - si valida, almacena secreto y marca `SECRET_STORED`.
- Si no hay password:
  - deja evidencia de evento `MAIL_INTAKE_PASSWORD_MISSING` para accion humana.

## Configuracion requerida (.env)
```env
CERTIFICATE_WORKFLOW_MAIL_INTAKE_ENABLED=true
CERTIFICATE_WORKFLOW_MAIL_INTAKE_POLL_SECONDS=120
CERTIFICATE_WORKFLOW_MAIL_INTAKE_IMAP_HOST=mail.getupsoft.com.do
CERTIFICATE_WORKFLOW_MAIL_INTAKE_IMAP_PORT=993
CERTIFICATE_WORKFLOW_MAIL_INTAKE_IMAP_USER=certificados@getupsoft.com.do
CERTIFICATE_WORKFLOW_MAIL_INTAKE_IMAP_PASS=***CHANGE_ME***
CERTIFICATE_WORKFLOW_MAIL_INTAKE_IMAP_MAILBOX=INBOX
CERTIFICATE_WORKFLOW_MAIL_INTAKE_USE_SSL=true
CERTIFICATE_WORKFLOW_MAIL_INTAKE_ALLOWED_SENDER_DOMAINS=ra.viafirma.do,viafirma.do
CERTIFICATE_WORKFLOW_MAIL_INTAKE_SUBJECT_CASE_REGEX=(PSC-\d{4}-\d{5})
CERTIFICATE_WORKFLOW_MAIL_INTAKE_ATTACHMENT_MAX_MB=20
CERTIFICATE_WORKFLOW_MAIL_INTAKE_AUTO_VALIDATE=true
CERTIFICATE_WORKFLOW_MAIL_INTAKE_PASSWORD_REGEX=(?i)(?:password|clave|passphrase)\s*[:=]\s*([^\s<>,;]+)
```

## Endpoint de disparo manual
```http
POST /api/v1/internal/certificate-workflow/mail-intake/process?limit=25
X-Internal-Secret: <HMAC_SERVICE_SECRET>
```

## Endpoint de salud IMAP (pre-check)
```http
GET /api/v1/internal/certificate-workflow/mail-intake/health
X-Internal-Secret: <HMAC_SERVICE_SECRET>
```

Respuesta esperada:
```json
{
  "enabled": true,
  "imap_host": "mail.getupsoft.com.do",
  "imap_port": 993,
  "mailbox": "INBOX",
  "use_ssl": true,
  "can_connect": true,
  "error": null
}
```

Respuesta:
```json
{
  "scanned": 10,
  "skipped_sender": 3,
  "skipped_case": 2,
  "attachments_saved": 4,
  "cases_updated": 4,
  "validations_ok": 2,
  "validations_failed": 2
}
```

## Requisitos Mailcow recomendados
1. Crear mailbox dedicado: `certificados@getupsoft.com.do`.
2. Habilitar IMAP SSL (993) y autenticacion de app password.
3. Reglas de filtro:
   - permitir remitentes `@ra.viafirma.do` y `@viafirma.do`;
   - mover correos no relacionados a carpeta aparte.
4. SPF/DKIM/DMARC correctos para evitar bloqueos de entrega.

## Nota Cloudflare Tunnel (`getupsoft.com.do`)
- El tunnel de Cloudflare aplica al trafico HTTP/HTTPS del hub (`api.getupsoft.com.do`, portales, callbacks web).
- La recepcion de correo por Mailcow (MX/SMTP/IMAP) no debe pasar por el tunnel HTTP.
- Recomendacion DNS para correo:
  - `MX getupsoft.com.do -> mail.getupsoft.com.do`
  - `A/AAAA mail.getupsoft.com.do` al host real de Mailcow (sin proxy naranja para puertos de correo).

## Nota operativa
- El flujo legal/humano (aceptacion contractual, validacion de identidad, pago y emision por PSC) no se automatiza.
- Si Viafirma no envia `case_id` en asunto/cuerpo, el correo se registra pero no se vincula automaticamente.
