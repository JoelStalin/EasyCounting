# Odoo ↔ EasyCounting Compatibility

## Matriz resumida

| EasyCounting / backend | Odoo 19 target | Regla |
| --- | --- | --- |
| `Tenant` | `res.company` | mapeo por tenant y `TenantSettings.odoo_company_id` |
| `Invoice.rnc_receptor` / receptor | `res.partner` | búsqueda por VAT, fallback por nombre |
| `Invoice` | `account.move` | `move_type=out_invoice`, `ref=encf`, `invoice_date=fecha_emision` |
| `InvoiceLine` | `invoice_line_ids` | comandos Odoo `0,0,values` |
| `tipo_ecf` | `l10n_latam_document_type_id` | mapeo por `TenantSettings` y reglas del localizador |
| `tax_total_source` / `itbis_amount` | `tax_ids` y tax lines | uso de tax ids configurados por tenant |
| `currency` | `currency_id` | mapping opcional por tenant |
| `estado_dgii` / `FiscalOperation.state` | `move state`, sync status | persistencia separada; no se mezcla estado fiscal con estado contable |

## Gaps cerrados

- Ruta Odoo → backend ahora reutiliza el pipeline DGII durable.
- Se agregaron campos Odoo por tenant.
- Se agregó cliente JSON-2 y mappers dedicados.

## Gaps externos pendientes

- Endpoint real Odoo 19, base de datos y API key no estaban configurados en el entorno auditado.
