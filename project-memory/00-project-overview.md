# Project Overview

- Proyecto auditado: `dgii_encf`
- Stack real: FastAPI, SQLAlchemy 2, PostgreSQL, Redis, React admin/client/seller portals, addons Odoo locales, integración DGII, Alembic, Docker Compose.
- Objetivo operativo: emisión y trazabilidad de e-CF, integración DGII, sincronización contable con Odoo 19 Enterprise y observabilidad técnica.
- Estado inicial auditado:
  - DGII real parcialmente implementado, pero rutas legacy fake seguían sombreando el flujo durable.
  - Dominio contable simplificado, sin equivalencia suficiente con `account.move`.
  - Persistencia de `TrackId` y estados insuficiente para reconstrucción integral.
  - Sin `project-memory/`.
  - Sin panel técnico consumiendo SSE; el monitoreo persistido existía de forma parcial.
- Estado después del endurecimiento:
  - Operación durable centralizada en `FiscalOperation`.
  - Flujo DGII real montado en `/api/dgii/*` y `/api/v1/dgii/*`.
  - Odoo transmit reutiliza el pipeline DGII durable.
  - Persistencia de eventos, intentos DGII/Odoo y artefactos.
  - Evidencia reproducible local en `tests/artifacts/2026-03-25_23-50-25_controlled_local_matrix/`.
