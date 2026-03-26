# DGII Integration Architecture

## Pipeline obligatorio implementado

1. `QUEUED`
2. `VALIDATING`
3. `BUILDING_PAYLOAD`
4. `SIGNING`
5. `SENDING_TO_DGII`
6. `DGII_RESPONSE_RECEIVED`
7. `TRACKID_REGISTERED`
8. `QUERYING_TRACK_STATUS`
9. `SYNCING_TO_ODOO`
10. `SYNCED_TO_ODOO`
11. `ACCEPTED | ACCEPTED_CONDITIONAL | REJECTED | FAILED_TECHNICAL | CANCELLED`

## Persistencia

- `FiscalOperation`
- `FiscalOperationEvent`
- `DGIIAttempt`
- `OdooSyncAttempt`
- `EvidenceArtifact`
- `ComprobanteCoverageResult`

## Evidencia

- XML firmado y hash
- respuesta inmediata DGII
- timeline técnico
- resumen de corrida

## Reintento

- Incremento de `retry_count`
- evento `RETRYING`
- reconsulta de `TrackId`
- re-sync Odoo si procede
