# Catalogo de Errores y Soluciones

Fuente machine-readable: `docs/certificados/autoasistido/error_catalog.json`.

Errores minimos tipados:

- `PORTAL_LOGIN_FAILED`
- `CAPTCHA_BLOCK`
- `SESSION_EXPIRED`
- `FORM_VALIDATION_ERROR`
- `UPLOAD_REJECTED`
- `SUBMIT_TIMEOUT`
- `TRACKID_MISSING`
- `DGII_STATUS_STALLED`

Politica base:

- Error UI transitorio: reintentar hasta 3 veces con backoff exponencial.
- Error legal/humano: bloquear y pasar a `HUMAN_APPROVAL_PENDING`.
- Error DGII de estado prolongado: escalar y dejar evidencia.
