# Servicio SMTP

El backend ahora incluye un servicio SMTP reusable en `app/services/email_service.py`.

Variables soportadas:

- `SMTP_HOST`
- `SMTP_PORT`
- `SMTP_USER`
- `SMTP_PASS`
- `SMTP_SECURE`
- `SMTP_FROM`
- `SMTP_TIMEOUT_SECONDS`

Comportamiento:

- `SMTP_SECURE=true` y puerto `465`: usa `SMTP_SSL`
- `SMTP_SECURE=true` y otro puerto: usa `STARTTLS`
- `SMTP_SECURE=false`: usa SMTP plano

Script de prueba:

```powershell
.\.venv\Scripts\python scripts\automation\send_test_email.py `
  --to tu-correo@dominio.com `
  --subject "Prueba SMTP" `
  --text "Mensaje de prueba"
```

Ejemplo de uso desde código:

```python
from app.services.email_service import EmailPayload, get_email_service

service = get_email_service()
service.send(
    EmailPayload(
        to="cliente@empresa.do",
        subject="Notificacion",
        text_body="Tu comprobante fue procesado.",
        html_body="<p>Tu comprobante fue procesado.</p>",
    )
)
```
