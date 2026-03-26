# Odoo Accounting Audit

## Evidencia local

- Addons Enterprise auditados fuera del repo.
- Addons de localización dominicana presentes en `integration/odoo/odoo19_getupsoft_do_localization/`.
- Catálogo de tipos documentales e-CF visible en:
  - `integration/odoo/odoo19_getupsoft_do_localization/getupsoft_l10n_do_e_accounting/data/l10n_latam.document.type.csv`
  - códigos `E31`, `E32`, `E33`, `E34`, `E41`, `E43`, `E44`, `E45`, `E46`, `E47`

## Hallazgos

- El backend original no tenía equivalencia suficiente con:
  - `res.partner`
  - `account.move`
  - `invoice_line_ids`
  - `l10n_latam_document_type_id`
  - impuestos / fiscal positions / payment terms
- La transmisión desde Odoo llegaba al backend, pero sin bridge durable completo ni sync JSON-2 real.

## Decisión aplicada

- El transporte externo objetivo para Odoo 19 queda en JSON-2.
- `InvoiceLedgerEntry` deja de ser la contabilidad maestra y pasa a read model auxiliar.
- `TenantSettings` absorbe el mapping Odoo necesario por tenant.
