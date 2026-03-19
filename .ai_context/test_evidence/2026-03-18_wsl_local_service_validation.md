# WSL Local Service Validation - 2026-03-18

## Objective

Levantar el backend del proyecto en WSL con puertos solo en loopback y validar el flujo funcional disponible sin exponer servicios publicamente.

## Runtime configuration applied

- `deploy/docker-compose.wsl-local.yml`
- `ops/nginx.local.conf`
- `scripts/automation/start_wsl_local_service.ps1`

Puertos locales esperados:

- `127.0.0.1:18000` -> FastAPI
- `127.0.0.1:18080` -> nginx local HTTP
- `127.0.0.1:15432` -> PostgreSQL
- `127.0.0.1:16379` -> Redis

## Verified observations

- `GET /health` sobre `127.0.0.1:18000` respondio `200` con `{"status":"ok"}`
- `GET /healthz` sobre `127.0.0.1:18080` respondio `200`
- `docker compose config` confirmo reemplazo real de puertos con `!override`
- `nginx` local quedo desacoplado de TLS para pruebas WSL

## Functional evidence

Command:

```powershell
.\.venv\Scripts\python -m pytest tests\test_e2e_local.py tests\test_enfc_endpoints.py tests\test_odoo_local_directory.py -q
```

Result:

- `12 passed in 4.95s`

Covered areas:

- flujo compat `auth -> recepcion -> status`
- endpoints ENFC `semilla`, `validacioncertificado`, `recepcion` y `aprobacioncomercial`
- busqueda local Odoo RNC por termino y por id fiscal

## Blockers for real DGII certification

- falta el certificado digital `.p12` del emisor y su password
- el usuario/password del portal DGII no reemplaza la firma del flujo `semilla -> validacioncertificado -> token`
- el stack WSL/Docker presento recreacion externa/intermitente del entorno host-bound, lo que impidio una validacion HTTP estable de larga duracion y tambien las migraciones hacia la DB local
