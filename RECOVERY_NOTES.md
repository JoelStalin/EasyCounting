# Recovery Notes — Pre-refactor snapshot (2026-03-30 03:15 UTC)

## 1) Estructura actual del proyecto (inventario)

### Módulos principales
- `app/main.py`: bootstrap FastAPI, middlewares, health checks y montaje de routers.
- `app/routers/*`: capa HTTP principal para portal admin/cliente/partner y flujos DGII.
- `app/api/*`: capa de compatibilidad y endpoints adicionales (`/api`, `/api/1`, ENFC, receptor, RI).
- `app/services/*`: servicios de negocio/transversales (autenticación, email, AI, DGII, idempotencia).
- `app/dgii/*`: dominio e infraestructura de firma/envío/consulta DGII.
- `app/certificate_workflow/*`: workflow de certificados, intake de correos, reminders y seguimiento.
- `app/models/*`, `app/domain/models/*`, `app/dgii/models/*`: modelos de persistencia y dominio.
- `app/db.py`: conexión y health de base de datos.
- `app/infra/settings.py`: configuración central por entorno.
- `app/jobs/*`: runners y jobs asíncronos.

### Endpoints detectados
- Total detectado automáticamente: **159** decoradores HTTP en `app/**/*.py`.
- Áreas clave:
  - Auth portal/API (`/auth/*`, `/api/v1/auth/*`, `/api/*`).
  - Cliente (`/api/v1/*` y legacy `/api/*`): facturas, chat, certificados, plan, tokens, Odoo.
  - Admin: tenants, planes, proveedores IA, KPIs, auditoría, billing.
  - DGII/ECF: recepción, aprobación, anulación, acuse, status/track.
  - Certificate workflow interno (`/api/v1/internal/*` y `/api/internal/*`).
  - Infra: `/health`, `/healthz`, `/livez`, `/readyz`, `/metrics`.

### Servicios
- Servicios de negocio ubicados en `app/services/` (ej. `auth_service.py`, `recepcion_service.py`, `aprobacion_service.py`, `email_service.py`, `dgii_client.py`).
- Servicios orientados a IA en `app/services/ai/*`.
- Servicios de certificación en `app/certificate_workflow/*`.

### Repositorios
- `app/auth/repository.py`.
- `app/dgii/infrastructure/dgii_submission_repository.py`.
- `app/dgii/infrastructure/signed_xml_repository.py`.
- Persistencia de workflow en `app/certificate_workflow/persistence.py`.

### Entidades/Modelos
- `app/models/*`: usuarios, tenant, facturas, auditoría, billing, memoria, etc.
- `app/dgii/models/*`: ECF/ARECF/ANECF/ACECF/RFCE en dominio DGII.
- `app/domain/models/*`: modelos de documentos fiscales.

### Configuraciones
- `app/infra/settings.py` (Pydantic Settings) + `.env`/`.env.local`.
- `alembic.ini` + `alembic/versions/*` para migraciones.
- `deploy/docker-compose*.yml`, `deploy/Dockerfile.*`, `docker/nginx.conf`.

### Dependencias
- Python/FastAPI stack en `pyproject.toml` y lock en `requirements.txt`.
- Dependencias críticas: FastAPI, SQLAlchemy, asyncpg/psycopg, pydantic-settings, signxml/lxml, redis/fastapi-limiter, prometheus instrumentator, sentry.

### Flujos críticos del negocio
1. Autenticación (login + MFA + social auth opcional).
2. Emisión y envío de ECF/ARECF/ACECF/ANECF/RFCE.
3. Consulta de estado/track de documentos DGII.
4. Gestión de tenants/planes/usuarios y proveedores IA.
5. Facturación cliente + recurrencia + envío por correo.
6. Firma XML y workflow de certificados.
7. Integración Odoo (sync e invoices).

## 2) Variables de entorno usadas (resumen)
Definidas principalmente en `app/infra/settings.py`:
- Runtime/API: `ENVIRONMENT`, `APP_NAME`, `CORS_ALLOW_ORIGINS`, dominios portal (`APP_PORTAL_DOMAIN`, `CLIENT_PORTAL_DOMAIN`, etc.).
- Seguridad/Auth: `JWT_SECRET`, expiraciones token, `MFA_ENABLED`, `SOCIAL_*`.
- Infra: `DATABASE_URL`, `REDIS_URL`, `SENTRY_DSN`, `LOG_LEVEL`, `RATE_LIMIT_PER_MINUTE`.
- DGII: `DGII_ENV`, `DGII_RNC`, URLs base DGII por entorno, polling/idempotencia.
- Correo: `SMTP_*`, `NOTIFY_*`.
- Certificados/workflow: `CERTIFICATE_WORKFLOW_*`, storage y secret provider.

## 3) Comandos para levantar el proyecto
- API local (si entorno preparado):
  - `uvicorn app.main:app --reload`
- Tests:
  - `pytest -q`
  - `pytest -q app/tests/e2e/test_endpoints.py`
- Docker (según entorno):
  - `docker compose -f deploy/docker-compose.yml up --build`

## 4) Línea base funcional (pre-refactor)

### Tests ejecutados
- `pytest -q app/tests/e2e/test_endpoints.py`
  - Resultado: **ERROR en colección** por dependencia faltante `pgvector` en el entorno local.
  - Riesgo: no hay baseline ejecutable completo sin resolver dependencias de runtime.

### Smoke checklist mínima (fallback)
Se creó checklist manual en `tests/functional/SMOKE_CHECKLIST_PRE_REFACTOR.md` para validar:
- autenticación,
- endpoints principales,
- operaciones críticas,
- persistencia,
- validaciones.

## 5) Riesgos conocidos antes del refactor
- Duplicidad de registro de routers versionados/legacy en `app/main.py` aumenta riesgo de inconsistencia.
- Acoplamiento alto en `app/main.py` (bootstrap, seguridad, jobs, y ruteo en un solo módulo).
- Baseline automatizada parcial por dependencia faltante (`pgvector`) en entorno de ejecución actual.

## 6) Pasos para restaurar backup
1. Restaurar estado Git:
   - `git checkout backup/pre-refactor-20260330-0315`
   - o `git checkout pre-refactor-stable-20260330-0315`
2. Restaurar copia física:
   - `rsync -a /backup/pre-refactor-20260330-0315/ /workspace/EasyCounting/`
3. Validar arranque/tests según sección de comandos.
