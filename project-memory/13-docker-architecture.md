# Docker Architecture

## Cambios

- `Dockerfile` no-root con `appuser`.
- build arg `INSTALL_BROWSER_AUTOMATION`.
- directorios persistentes:
  - `/var/getupsoft/storage`
  - `/app/tests/artifacts`
  - `/app/logs`
- `docker-compose.yml` endurecido con:
  - healthcheck `readyz`
  - healthcheck Redis
  - volúmenes de storage y artifacts
  - `TZ`
  - `security_opt: no-new-privileges:true`

## Validación local cerrada

- `docker compose up -d db redis web`
- `curl http://localhost:8000/readyz` => `{"status":"ready","checks":{"database":true,"redis":true}}`
- Evidencia: `tests/artifacts/2026-03-25_23-50-25_controlled_local_matrix/docker-validation.json`
