# Runbook operadores certificados DGII

## Incidente: password PKCS#12 incorrecta
- Sintoma: `PKCS#12 invalido o password incorrecto`.
- Verificacion: ejecutar `validate_dgii_p12.py`.
- Mitigacion inmediata: solicitar password por canal seguro.
- Correccion permanente: doble control de carga y checklist de handoff.

## Incidente: certificado vencido
- Sintoma: `Certificado fuera de vigencia`.
- Verificacion: revisar `not_after` y fecha UTC actual.
- Mitigacion inmediata: bloquear uso en firma.
- Correccion permanente: iniciar renovacion con alertas 30/15/7 dias.

## Incidente: subject no coincide
- Sintoma: `Subject de certificado no coincide`.
- Verificacion: comparar subject real con delegado/RNC esperado.
- Mitigacion inmediata: detener activacion.
- Correccion permanente: ajustar control de identidad en intake.

## Incidente: caso bloqueado en HUMAN_SUBMISSION_PENDING
- Sintoma: no avanza por mas de 72h.
- Verificacion: revisar expediente en `06-seguimiento/`.
- Mitigacion inmediata: escalar a responsable fiscal.
- Correccion permanente: automatizar recordatorios y SLA.

## Evidencia minima obligatoria
- Resultado JSON de precheck.
- Resultado JSON de validacion de certificado.
- Hash SHA-256 del archivo cargado.
- Operador, timestamp y `case_id`.

## Operacion continua TrackId (autopoll)
- Job activo: `CERTIFICATE_WORKFLOW_REMINDER_JOB_ENABLED=true` (mismo runner ejecuta reminders + track poll).
- Modo live DGII: `CERTIFICATE_WORKFLOW_TRACK_POLL_LIVE=true` solo en ambientes preparados.
- Limite por ciclo: `CERTIFICATE_WORKFLOW_TRACK_POLL_LIMIT` (default `25`).
- Endpoint manual interno: `POST /api/v1/internal/certificate-workflow/track-status/process-ready`.

## Incidente: TrackId estancado en EN_PROCESO
- Sintoma: eventos repetidos `DGII_TRACK_AUTOPOLL_OK` sin estado terminal.
- Verificacion: revisar eventos del `case_id` y status DGII acumulado.
- Mitigacion inmediata: ejecutar poll manual `GET /track-status/poll` con `max_attempts` mayor.
- Correccion permanente: ajustar ventana de reintentos e investigar reglas de rechazo DGII.
