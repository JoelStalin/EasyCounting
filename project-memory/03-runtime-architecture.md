# Runtime Architecture

## Backend

- Entrada principal: `app/main.py`
- API versionada: `/api/v1`
- Compatibilidad legacy: `/api`
- Jobs: dispatcher DGII y recurring invoices controlados por `JOBS_ENABLED`
- Persistencia: PostgreSQL en runtime; SQLite controlado para evidencia local

## Flujo DGII endurecido

1. Router DGII recibe payload.
2. `submit_ecf()` crea `FiscalOperation`.
3. Se valida billing y XML.
4. Se firma XML.
5. Se persiste `Invoice`, `InvoiceLine`, intento DGII y evidencia.
6. Se envía a DGII.
7. Se persiste `TrackId`.
8. Job de consulta actualiza estado remoto y puede disparar sync a Odoo.

## Flujo Odoo endurecido

- `app/infrastructure/odoo/json2_client.py`: transporte JSON-2.
- `app/infrastructure/odoo/mappers.py`: partner/account.move/taxes/document types.
- `app/application/accounting_sync.py`: sincronización durable.
- `app/routers/odoo.py`: entrada operativa desde Odoo reutilizando el pipeline DGII durable.

## Observabilidad

- `FiscalOperationEvent`: timeline persistido.
- `DGIIAttempt`, `OdooSyncAttempt`: intentos técnicos.
- `EvidenceArtifact`: archivos durables.
- `GET /api/v1/operations/{id}/stream`: SSE snapshot/tail según `Accept`.
- Admin portal: monitor técnico por polling controlado y eventos persistidos.
