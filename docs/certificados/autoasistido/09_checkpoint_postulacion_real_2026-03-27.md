# 09 - Checkpoint Postulacion Real DGII (2026-03-27)

## Certificado confirmado para pruebas reales
- Ruta de certificado provista por operador:
  - `C:\Users\yoeli\Documents\dgii_encf\app\dgii\certf\20260327-1854064-YNKAE7HKQ.p12`

## Requisito funcional previo (cerrado en codigo)
- Se unifico regla de formato e-NCF para emisiones desde:
  - portal cliente (tenant API / hub),
  - recepcion desde Odoo (`/api/v1/odoo/invoices/transmit`).
- Regla aplicada:
  - `E` + tipo (2 digitos) + secuencial (10 digitos).
  - Ejemplo: `E310000000005`.

## Estado de mail intake (para retomar)
- Implementado y pendiente de activacion productiva:
  - health: `GET /api/v1/internal/certificate-workflow/mail-intake/health`
  - proceso: `POST /api/v1/internal/certificate-workflow/mail-intake/process`

## Siguiente paso operativo
1. Ejecutar smoke de emision (portal cliente y Odoo) para verificar secuencia e-NCF.
2. Con variables reales (`DGII_REAL_USERNAME`, `DGII_REAL_PASSWORD`, password p12), ejecutar `run_real_dgii_postulacion_ofv.py`.
3. Guardar evidencia del run en `tests/artifacts/*_dgii_real_postulacion_ofv`.
