# Real Environment Guardrails

Fecha: `2026-03-18`

## Decision

No se usaron las credenciales DGII reales ni la cuenta root de AWS compartidas en la conversacion.

## Razon

- alto riesgo operativo y de seguridad
- la cuenta root de AWS no debe usarse para CLI automatizada
- los secretos divulgados deben considerarse comprometidos y deben rotarse

## Entregables seguros

- `deploy/docker-compose.wsl-local.yml`
- `scripts/automation/start_wsl_local_service.ps1`
- `scripts/automation/stop_wsl_local_service.ps1`
- `scripts/automation/configure_aws_route53_profile.ps1`
- `scripts/automation/update_route53_getupsoft.ps1`
- `scripts/automation/REAL_CERTIFICATION_RUNBOOK.md`

## Ajuste posterior

- el compose local WSL fue corregido para reemplazar los puertos base con `!override`
- los binds locales quedaron en `127.0.0.1:18000`, `18080`, `15432` y `16379`
- para WSL local se agrego `ops/nginx.local.conf` sin dependencia de certificados TLS
- el perfil AWS admite `SessionToken` para credenciales temporales IAM
