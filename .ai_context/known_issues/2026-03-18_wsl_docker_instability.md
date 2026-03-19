# WSL Docker Instability - 2026-03-18

## Symptom

El stack local en WSL fue recreado externamente en varias ocasiones durante la validacion. Los contenedores aparecian como `Up 2 seconds` repetidamente y las conexiones host-bound a `127.0.0.1:18000` y `127.0.0.1:15432` fallaban de forma intermitente.

## Evidence

- `docker compose ps` mostro reinicios/recreaciones repetidas de `web`, `db` y `nginx`
- el intento de `alembic upgrade head` contra `127.0.0.1:15432` fallo con `ConnectionRefusedError`
- las llamadas HTTP desde Windows al backend levantado en WSL fueron inestables a pesar de que `health` y `healthz` respondieron correctamente en comprobaciones puntuales

## Suspected cause

- un proceso externo de Docker/WSL o una recreacion automatica del stack fuera del flujo normal de trabajo

## Impact

- bloquea una corrida host-bound estable del flujo completo
- impide migrar la base local con confianza
- retrasa la preparacion de una certificacion DGII `CERT` desde este host

## Next checks

- confirmar que no quede ningun proceso residual ejecutando `docker compose up`
- revisar el estado del motor Docker Desktop y de la integracion WSL
- estabilizar el bind local antes de repetir `alembic upgrade head`
- luego cargar el `.p12` real y ejecutar certificacion DGII sobre el backend estable
