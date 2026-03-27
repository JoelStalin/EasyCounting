# Checkpoints y Reanudacion

## Entidades

- `workflow_executions`
- `workflow_step_logs`

## Endpoints

- `POST /api/v1/internal/certificate-workflow/{case_id}/execution/start`
- `POST /api/v1/internal/certificate-workflow/{case_id}/checkpoint`
- `GET /api/v1/internal/certificate-workflow/{case_id}/progress`
- `POST /api/v1/internal/certificate-workflow/{case_id}/resume`

## Regla operativa

- Solo confirmar paso completado cuando exista evidencia (`screenshot_path` o `artifact_path` o `details`).
- Si el paso requiere accion humana/legal: registrar `FAILED_BLOCKED` y `current_step=HUMAN_APPROVAL_PENDING`.
- Reanudar siempre desde `last_success_step`.
