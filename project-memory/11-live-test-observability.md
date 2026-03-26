# Live Test Observability

## Backend

- `GET /api/v1/operations`
- `GET /api/v1/operations/{operation_id}`
- `GET /api/v1/operations/{operation_id}/events`
- `GET /api/v1/operations/{operation_id}/stream`
- `POST /api/v1/operations/{operation_id}/retry`

## Estado técnico visible

- `operation_id`
- `correlation_id`
- `environment`
- `state`
- `dgii_track_id`
- `odoo_sync_state`
- eventos persistidos por etapa
- evidencia asociada

## UI técnica

- `frontend/apps/admin-portal/src/components/OperationMonitor.tsx`
- polling controlado sobre eventos persistidos
- SSE backend disponible para clientes que pidan `text/event-stream`

## Validación local

- El script `scripts/run_local_controlled_matrix.py` verificó:
  - listado
  - detalle
  - eventos
  - stream SSE snapshot
