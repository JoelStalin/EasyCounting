# DGII e-CF Plataforma Lista para Producción

Backend FastAPI (Python 3.12) listo para desplegar en producción con Docker, Gunicorn/Uvicorn, Nginx, PostgreSQL, Redis y observabilidad integrada.

## Arquitectura

```
[Internet]
    |
[NGINX reverse proxy]
    |
[Gunicorn (UvicornWorker) -> FastAPI]
    |--> PostgreSQL 16 (SQLAlchemy async + Alembic)
    |--> Redis 7 (rate limit & background primitives)
    |--> Observabilidad: Prometheus metrics, JSON logs, Sentry
```

## Requisitos previos

- Docker / Docker Compose v2
- Python 3.12 + Poetry (para desarrollo local)
- Acceso a un registro de contenedores (ej. `ghcr.io/getupsoft`)

## Puesta en marcha

```bash
poetry install --sync  # o bien: pip install -r requirements-dev.txt
make requirements      # exporta requirements.txt para la imagen
make up                # levanta web + nginx + postgres + redis usando `.env.example`
```

¿Quieres sobreescribir variables locales? Crea un archivo alternativo y apúntalo vía `ENV_FILE`:

```bash
cp .env.example .env.local
ENV_FILE=.env.local make up
```

Servicios expuestos:

- `http://localhost:8080` → Nginx → FastAPI
- `http://localhost:8080/livez` → liveness
- `http://localhost:8080/readyz` → readiness (verifica DB/Redis)
- `http://localhost:8080/metrics` → Prometheus

Para detener y limpiar:

```bash
make down
```

## Desarrollo local

### Rutas de prueba

```bash
# Cliente
curl -sS http://localhost:8000/cliente/health | jq
curl -sS -H "Authorization: Bearer cliente:alice" http://localhost:8000/cliente/me | jq
curl -sS -H "Authorization: Bearer cliente:alice" http://localhost:8000/cliente/facturas | jq

# Administrador (requiere rol admin)
curl -sS -H "Authorization: Bearer admin:bob" http://localhost:8000/admin/health | jq
curl -sS -H "Authorization: Bearer admin:bob" http://localhost:8000/admin/usuarios | jq
curl -sS -H "Authorization: Bearer admin:bob" -H "Content-Type: application/json" \
     -d '{"ncf":"E3100000001"}' http://localhost:8000/admin/facturas/aprobar | jq
```

## Comandos útiles

| Comando | Descripción |
| --- | --- |
| `make up` | Levanta la pila dockerizada.
| `make down` | Detiene y elimina contenedores/volúmenes.
| `make logs` | Sigue los logs del servicio `web`.
| `make migrate` | Ejecuta `alembic upgrade head` dentro del contenedor.
| `make test` | Ejecuta el suite de pruebas (`pytest`).
| `make lint` | Valida el estilo con Ruff.
| `make requirements` | Exporta dependencias pinneadas para Docker.

## Variables de entorno

| Variable | Descripción | Valor por defecto |
| --- | --- | --- |
| `APP_NAME` | Nombre expuesto en OpenAPI. | `DGII e-CF API` |
| `ENVIRONMENT` | Entorno actual (`development`, `staging`, `production`). | `development` |
| `DATABASE_URL` | URL SQLAlchemy async (`postgresql+asyncpg://`). | `postgresql+asyncpg://dgii:dgii@db:5432/dgii` |
| `REDIS_URL` | URL Redis para rate limit / colas. | `redis://redis:6379/0` |
| `CORS_ALLOW_ORIGINS` | Orígenes permitidos (lista separada por comas). | `https://api.dgii.getupsoft.com.do,https://staging.dgii.getupsoft.com.do` |
| `RATE_LIMIT_PER_MINUTE` | Límite global por IP. | `100` |
| `SENTRY_DSN` | DSN de Sentry (opcional). | — |
| `SENTRY_TRACES` | Ratio de muestreo para APM. | `0.0` |
| `JWT_SECRET` | Secreto para JWT corto. | `change-me` |
| `DGII_*` | URLs/credenciales DGII legadas. | Ver `.env.example` |

## Observabilidad y seguridad

- Logs JSON (`structlog`) enviados a stdout y consumidos por Docker/Stackdriver.
- `/metrics` expuesto por `prometheus-fastapi-instrumentator`.
- Integración Sentry opcional (no falla si falta `SENTRY_DSN`).
- CORS restringido a dominios productivos y `TrustedHostMiddleware` con allow-list.
- Rate limiting 100 req/min/IP vía `fastapi-limiter` + Redis.
- Cabeceras seguras (CSP, X-Frame-Options, etc.) añadidas a cada respuesta.

## Migraciones con Alembic

```bash
poetry run alembic revision -m "titulo"
poetry run alembic upgrade head
```

La carpeta `alembic/versions/` contiene un ejemplo de migración inicial. El `docker-compose` ejecuta PostgreSQL 16 y persiste datos en el volumen `pgdata`.

## CI/CD (GitHub Actions)

El workflow `.github/workflows/ci-cd.yml` ejecuta:

1. Lint + pruebas (`pytest`).
2. Construcción de la imagen Docker y push a `${{ github.repository }}/web` (modifica `IMAGE` según tu registro).
3. Paso de despliegue: placeholder via webhook/SSH (ajusta a tu infraestructura).

Variables necesarias en GitHub Secrets:

- `REGISTRY_USER` / `REGISTRY_PAT`
- `DEPLOY_TOKEN` (para el webhook de despliegue)

## Endurecimiento Nginx

`ops/nginx.conf` actúa como reverse proxy con:

- Soporte WebSocket.
- Gzip y límites de payload (`client_max_body_size 16m`).
- Cabeceras seguras (X-Content-Type-Options, X-Frame-Options, etc.).
- TLS opcional: añade certificado y `Strict-Transport-Security` cuando termines SSL en Nginx.

## Troubleshooting

| Síntoma | Posible causa / solución |
| --- | --- |
| `/readyz` devuelve 503 | Verifica PostgreSQL/Redis; revisa logs de `web`. |
| Gunicorn reinicia | Ajusta `GUNICORN_MAX_REQUESTS` o revisa out-of-memory. |
| No se exportan métricas | Confirma que `prometheus-fastapi-instrumentator` no esté deshabilitado por env (`PROMETHEUS_DISABLED`). |
| Error de certificados DGII | Monta el `.p12` en `/secrets` y revisa `DGII_P12_PASSWORD`. |

## Despliegue TLS

1. Genera/instala certificados en el host (`/etc/letsencrypt/...`).
2. Monta en el contenedor Nginx y habilita:
   ```nginx
   listen 443 ssl http2;
   ssl_certificate /etc/nginx/tls/fullchain.pem;
   ssl_certificate_key /etc/nginx/tls/privkey.pem;
   add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
   ```
3. Redirige puerto 80 → 443 y renueva con `certbot` según tu flujo.

---

Para dudas adicionales consulta `docs/` o abre un issue.
