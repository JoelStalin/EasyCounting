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
    |--> Browser MCP sidecar (Playwright MCP + jobs API)
    |--> Observabilidad: Prometheus metrics, JSON logs, Sentry
```

## Requisitos previos

- Docker / Docker Compose v2
- Python 3.12 + Poetry (para desarrollo local)
- Acceso a un registro de contenedores (ej. `ghcr.io/getupsoft`)

## Puesta en marcha

```bash
poetry install --sync --no-root  # o bien: pip install -r requirements-dev.txt
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

### Browser MCP sidecar

La capa de navegador productiva vive en [automation/browser-mcp/README.md](/c:/Users/yoeli/Documents/dgii_encf/automation/browser-mcp/README.md).

Comandos base:

```bash
cd automation/browser-mcp
npm install
npm run browsers:install
npm run build
npm run mcp:http
```

Para que FastAPI use el sidecar:

```bash
export BROWSER_MCP_ENABLED=true
export BROWSER_MCP_MODE=remote
export BROWSER_MCP_BASE_URL=http://browser-mcp:8930
```

Para flujos DGII repetibles con perfil real clonado y navegador normal:

```bash
export BROWSER_MCP_DEFAULT_BROWSER=chromium
export BROWSER_MCP_CHROMIUM_CHANNEL=chrome
export DGII_CHROME_PROFILE_SOURCE=Default
export DGII_POSTULACION_POLICY_BASELINE=strict_normal_browser
```

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

## Firma XML DGII (postulacion y e-CF)

La firma XML se ejecuta con perfil DGII:

- `XMLDSIG enveloped`
- `CanonicalizationMethod=C14N 1.0` (`http://www.w3.org/TR/2001/REC-xml-c14n-20010315`)
- `SignatureMethod=RSA-SHA256`
- `DigestMethod=SHA-256`
- `Reference URI=""`
- `KeyInfo/X509Data/X509Certificate` embebido

Configuracion:

| Variable | Descripcion |
| --- | --- |
| `DGII_SIGNING_MODE` | `pfx`, `windows-store`, `external` |
| `DGII_PFX_PATH` | Ruta al archivo `.p12/.pfx` |
| `DGII_PFX_PASSWORD` | Password del `.p12/.pfx` |
| `DGII_CERT_THUMBPRINT` | Thumbprint para Windows Certificate Store |
| `DGII_CERT_STORE_LOCATION` | `CurrentUser` o `LocalMachine` |
| `DGII_CERT_STORE_NAME` | Store name, por defecto `My` |
| `DGII_SIGN_TARGET_TAG` | Nodo objetivo a firmar (`ECF`, `RFCE`, etc.) |
| `DGII_VALIDATE_SIGNATURE` | `true/false` validacion posterior de firma |

### Modo PFX

1. Cargar certificado del tenant por API (`/api/v1/cliente/certificates`) o por variables de entorno.
2. Firmar XML por flujo interno (`TenantCertificateService`) o por endpoint (`/api/v1/cliente/certificates/sign-xml`).

### Modo Windows Certificate Store

1. Instalar certificado del representante en `CurrentUser\My` o `LocalMachine\My`.
2. Definir `DGII_SIGNING_MODE=windows-store`.
3. Definir `DGII_CERT_THUMBPRINT`, `DGII_CERT_STORE_LOCATION` y `DGII_CERT_STORE_NAME`.
4. El backend usa `scripts/automation/sign_with_windows_certstore.ps1`.

### Modo External (stub)

`DGII_SIGNING_MODE=external` deja listo el contrato de integracion, pero no firma aun. El sistema responde error controlado indicando que falta conectar App Firma Digital o un servicio externo.

### Ejemplo de ejecucion simulada

```bash
poetry run pytest tests/test_xml_dsig_service.py -q
```

## Troubleshooting firma DGII

- Error `La firma utilizada en el XML no corresponde con el representante registrado`:
  - La firma puede ser criptograficamente valida, pero DGII la rechaza por identidad tributaria.
  - Debes usar el certificado real del representante legal registrado para ese RNC.
- Diferencia clave:
  - Valida criptograficamente: XMLDSIG correcto (algoritmos, digest, cadena de firma).
  - Aceptada por DGII: ademas coincide la identidad fiscal del certificado con el contribuyente/representante.
- Verificar certificado antes de firmar:
  - `Subject`, `Issuer`, `Thumbprint`, `notBefore`, `notAfter`.
  - Si no existe en `CurrentUser\My` o `LocalMachine\My`, importar el certificado correcto.
- Errores comunes manejados por la API:
  - certificado no encontrado
  - certificado sin llave privada
  - password incorrecto
  - certificado expirado/no vigente
  - thumbprint invalido
  - XML mal formado
  - validacion de firma fallida

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

1. Pruebas (`pytest`) y validación de export de dependencias.
2. Construcción de la imagen de API con `deploy/Dockerfile.api` y push a `ghcr.io/getupsoft/dgii-ecf`.
3. Despliegue productivo por webhook autenticado hacia `deploy/server/deploy_hook.py`, que en el host hace `git pull`, recompila los portales y reinicia `docker compose`.

Variables necesarias en GitHub Secrets:

- `REGISTRY_USER` / `REGISTRY_PAT`
- `DEPLOY_WEBHOOK_URL`
- `DEPLOY_TOKEN` (para el webhook de despliegue)

La configuración del host productivo versionada vive en `deploy/server/`:

- `deploy_hook.py`: webhook `POST /deploy`
- `deploy.sh`: flujo de despliegue en el servidor
- `docker-compose.server.yml`: stack productivo
- `nginx.conf`: virtual hosts y proxy para API/webhook
- `deploy-hook.env.example`: variables requeridas por el servicio systemd

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

## Límites reales del sistema

- Playwright MCP mejora control, trazabilidad y persistencia de sesión, pero no elimina controles reales del navegador o del sitio.
- No se debe asumir bypass de CAPTCHA, anti-bot, CORS, autenticación federada o políticas del portal objetivo.
- Los flujos DGII/Odoo reales deben ejecutarse con credenciales válidas, ambientes autorizados y evidencia guardada por job.

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
