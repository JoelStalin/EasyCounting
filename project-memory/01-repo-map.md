# Repo Map

## Top level

- `app/`: backend FastAPI, dominio, routers, seguridad, observabilidad, integración DGII/Odoo.
- `frontend/apps/admin-portal/`: portal técnico/admin.
- `integration/odoo/`: addons Odoo 15/19 y localización dominicana.
- `automation/browser/`: módulo controlado de browser automation.
- `alembic/`: migraciones.
- `tests/`: unitarias, integración y artefactos.
- `ops/`: plantillas de despliegue y Nginx.
- `labs/odoo19_chefalitas/`: laboratorio Odoo local auditado.

## Backend slices

- `app/application/`: servicios de caso de uso.
- `app/infrastructure/odoo/`: cliente JSON-2, mappers y reconciliación.
- `app/dgii/`: cliente, signing, jobs, schemas y retry.
- `app/models/`: modelos SQLAlchemy.
- `app/observability/`: artefactos y SSE.
- `app/routers/`: API operativa nueva.
- `app/api/routes/`: compatibilidad legacy; contiene router DGII fake que fue relegado detrás de las rutas reales.

## Key files for this hardening

- `app/application/ecf_submission.py`
- `app/application/fiscal_operations.py`
- `app/application/accounting_sync.py`
- `app/dgii/jobs.py`
- `app/models/fiscal_operation.py`
- `app/models/invoice.py`
- `app/models/accounting.py`
- `app/infrastructure/odoo/json2_client.py`
- `app/observability/live_stream.py`
- `app/routers/operations.py`
- `app/routers/odoo.py`
- `app/main.py`
