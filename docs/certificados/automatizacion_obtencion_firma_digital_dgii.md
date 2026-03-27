# Automatizacion obtencion firma digital DGII

## Alcance implementado en este repo

Este repositorio ya incluye automatizacion tecnica para:

- intake estructurado del caso;
- precheck interno obligatorio;
- generacion de expediente por `case_id`;
- validacion tecnica de certificado `.p12/.pfx`;
- salida JSON compatible con flujos de n8n/Make/GitHub Actions.

La emision legal del certificado con PSC sigue siendo una tarea humana auditada.

## Scripts nuevos

- `scripts/automation/certificate_workflow_cli.py`
  - Lee un JSON de intake.
  - Genera `case_id`.
  - Ejecuta precheck.
  - Crea expediente local con artefactos base.
- `scripts/automation/validate_dgii_p12.py`
  - Valida PKCS#12 con `CertificateProvider`.
  - Emite resultado JSON.
  - Devuelve `exit code 0` si el certificado es valido.

## API interna (persistencia DB)

Endpoints protegidos por `X-Internal-Secret`:

- `POST /api/v1/internal/certificate-workflow/intake`
- `GET /api/v1/internal/certificate-workflow/{case_id}`
- `POST /api/v1/internal/certificate-workflow/{case_id}/validate-certificate`
- `POST /api/v1/internal/certificate-workflow/{case_id}/status`
- `POST /api/v1/internal/certificate-workflow/{case_id}/reminders`
- `GET /api/v1/internal/certificate-workflow/reminders/due`
- `POST /api/v1/internal/certificate-workflow/reminders/{reminder_id}/resolve`
- `POST /api/v1/internal/certificate-workflow/reminders/process-due`
- `POST /api/v1/internal/certificate-workflow/{case_id}/store-secret`
- `POST /api/v1/internal/certificate-workflow/{case_id}/smoke-sign`
- `POST /api/v1/internal/certificate-workflow/{case_id}/dgii-certification-check`
- `POST /api/v1/internal/certificate-workflow/{case_id}/submit-test-ecf`
- `GET /api/v1/internal/certificate-workflow/{case_id}/track-status`
- `GET /api/v1/internal/certificate-workflow/{case_id}/track-status/poll`
- `POST /api/v1/internal/certificate-workflow/track-status/process-ready`

Tablas creadas por migracion:

- `psc_requests`
- `workflow_events`
- `certificate_validations`
- `workflow_reminders`

Job de background:
- `certificate_workflow_reminder_runner` procesa recordatorios vencidos cada `CERTIFICATE_WORKFLOW_REMINDER_POLL_SECONDS`.
- El mismo runner procesa auto-poll de `TrackId` para casos `READY_FOR_DGII`.
  - `CERTIFICATE_WORKFLOW_TRACK_POLL_LIVE` controla si consulta DGII real.
  - `CERTIFICATE_WORKFLOW_TRACK_POLL_LIMIT` controla volumen por ciclo.

Smoke sign:
- Usa `secret_ref` almacenado.
- Firma XML de prueba.
- Verifica firma local.
- Si pasa, transiciona automaticamente a `READY_FOR_DGII`.

DGII certification check:
- Modo `simulated` (default): no hace llamadas externas, solo evidencia y trazabilidad.
- Modo `live=true`: intenta `bearer()` DGII y `consulta_directorio(rnc)`.
- Puede transicionar a `IN_PRODUCTION_USE` con `transition_to_in_production=true`.

Submit y TrackId:
- `submit-test-ecf` firma XML y simula/envia a DGII, registrando `TrackId` en eventos.
- `track-status` consulta estado de un `TrackId` especifico o inferido de eventos.
- `track-status/poll` reintenta con `max_attempts`/`interval_ms` y detecta estados terminales.
- Si resultado terminal es `ACEPTADO`, el caso puede pasar automaticamente a `IN_PRODUCTION_USE`.

## Ejemplo intake

```json
{
  "rnc": "131234567",
  "razon_social": "Empresa Demo SRL",
  "tipo_contribuyente": "juridica",
  "delegado_nombre": "Juan Perez",
  "delegado_identificacion": "00112345678",
  "delegado_correo": "juan.perez@empresa.com",
  "delegado_telefono": "8095551234",
  "delegado_cargo": "Gerente",
  "psc_preferida": "AVANSI",
  "usa_facturador_gratuito": false,
  "ofv_habilitada": true,
  "alta_ncf_habilitada": true,
  "responsable_ti": "ti@empresa.com",
  "responsable_fiscal": "fiscal@empresa.com",
  "ambiente_objetivo": "test"
}
```

## Uso

```bash
python scripts/automation/certificate_workflow_cli.py --input intake.json --output-dir expedientes
```

```bash
python scripts/automation/validate_dgii_p12.py \
  --file /ruta/certificado.p12 \
  --password '***' \
  --expected-rnc 131234567
```

## Estructura de expediente

```text
expedientes/
  PSC-YYYY-MMDDHHMMSS/
    01-resumen-caso.md
    02-datos-contribuyente.json
    03-datos-delegado.json
    04-checklist-documental.md
    05-evidencias/
    06-seguimiento/precheck.json
    07-certificado/
```

## Criterio de readiness

Un caso pasa a readiness tecnico cuando:

- precheck = `PRECHECK_OK`;
- certificado = valido en `validate_dgii_p12.py`;
- certificado cargado en secret manager (proceso operativo externo);
- smoke test de firma XML exitoso.

## Autoasistido y crecimiento

- Workflow n8n base: `automation/n8n/workflows/dgii_postulacion_autoasistida_v1.json`.
- Stack dual browser:
  - Selenium: `scripts/automation/run_real_dgii_postulacion_ofv.py`
  - Playwright: `app/dgii_portal_automation/*`
  - Contrato unificado: `scripts/automation/run_portal_task.py`
- Checkpoint y reanudacion:
  - `POST /execution/start`
  - `POST /checkpoint`
  - `GET /progress`
  - `POST /resume`
