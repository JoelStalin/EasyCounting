# Evidencia modo real Odoo -> Hub -> DGII

Fecha corrida: 2026-03-27
Artifacts: `docs/evidence/odoo_matrix_20260327_085547`

## Resultado funcional Odoo
- Facturas creadas/posteadas en Odoo: 14/14
- Tipos: B01, B02, B03, B04, E31, E32, E33, E34, E41, E43, E44, E45, E46, E47

## Resultado integración real
- Endpoint Odoo->Hub respondió `500 Internal Server Error` para las 14 transmisiones de la corrida real.
- Causa técnica en backend: `app.dgii.exceptions.DGIIRetryableError: Error de comunicación con DGII`.
- Punto de falla: llamada a semilla DGII (`https://ecf.dgii.gov.do/TesteCF/Autenticacion/semilla`) con desconexión remota.

## Evidencia de logs
- Odoo errores de transmisión: `odoo_real_mode_errors.log`
- Hub excepción DGII: `hub_real_mode_errors.log`
- Nginx códigos HTTP 500: `nginx_real_mode_500.log`

## PDF evidencia visual
- `docs/evidence/odoo_facturas_evidencia_real_mode_20260327_085832.pdf`

## Nota
El flujo de negocio Odoo + módulo local quedó operando; el bloqueo actual es conectividad/estabilidad del endpoint DGII en modo real, no mapeo de comprobantes ni creación de factura.
