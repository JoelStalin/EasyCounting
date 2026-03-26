# Security Model

## Aplicado

- Secrets fuera del repo; plantillas `.env` endurecidas.
- Certificados montados por ruta `/secrets`.
- `request_id` y `trace_id` sin exponer secretos.
- Panel técnico protegido por rol `platform_admin`.
- Browser automation desactivado por defecto.
- Docker no-root y `no-new-privileges`.

## No permitido

- Tokens DGII al frontend
- Cookies persistidas del navegador sin control
- Certificados reales commiteados
- bypass de controles del portal DGII

## Bloqueos externos auditados

- `secrets/cert.p12` real ausente
- credenciales DGII portal vacías
- `DGII_P12_PASSWORD` placeholder en entorno auditado
