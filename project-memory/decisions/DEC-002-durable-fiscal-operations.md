# DEC-002 Durable Fiscal Operation as System of Record

- Fecha: 2026-03-25
- Tema: trazabilidad y coordinación DGII/Odoo
- Fuente:
  - https://dgii.gov.do/cicloContribuyente/facturacion/comprobantesFiscalesElectronicosE-CF/Paginas/documentacionSobreE-CF.aspx
  - https://www.odoo.com/documentation/19.0/applications/finance/accounting.html
- Conclusión práctica:
  - Cada envío DGII y sync Odoo se modela como `FiscalOperation`.
  - `TrackId`, eventos, intentos, reintentos y evidencia se persisten por operación.
- Archivos afectados:
  - `app/models/fiscal_operation.py`
  - `app/application/fiscal_operations.py`
  - `app/application/ecf_submission.py`
  - `app/dgii/jobs.py`
- Impacto:
  - Reconstrucción completa de operaciones y eliminación de estados silenciosos.
