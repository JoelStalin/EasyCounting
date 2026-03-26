# Stability Hardening

## Reglas aplicadas

- Estados durables por operación.
- Idempotencia por `operation_key`.
- Precisión decimal fiscal/contable `Numeric(20,6)`.
- Persistencia de evidencia y hashes.
- Correlación por `request_id` y `trace_id`.
- Retry controlado y explicitado en modelo.
- Separación explícita de ambientes DGII.
- Session factory overridable para pruebas y procesos fuera de request.

## Archivos clave

- `app/application/fiscal_operations.py`
- `app/application/ecf_submission.py`
- `app/shared/database.py`
- `app/observability/live_stream.py`
- `app/infra/settings.py`
