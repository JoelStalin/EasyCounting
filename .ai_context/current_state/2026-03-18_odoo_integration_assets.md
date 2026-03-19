# Odoo Integration Assets - 2026-03-18

## Imported asset

- Local path: `integration/odoo/neo_do_localization`
- Source host: `jabiya`
- Source path: `/opt/odoo-docker/addons/neo_do_localization`
- Source commit: `64708451b8d64173c52c222f66dfb39ef9abfae2`

## Modules present

- `l10n_do_accounting`
- `l10n_do_accounting_report`
- `l10n_do_e_accounting`
- `l10n_do_pos`
- `l10n_do_rnc_search`

## Local adaptation layer

- `integration/odoo/README.md`
- `integration/odoo/neo_do_localization/README.md`
- `integration/odoo/neo_do_localization/SOURCE_METADATA.md`
- `integration/odoo/neo_do_localization/GETUPSOFT_MAPPING.md`
- `integration/odoo/neo_do_localization/getupsoft_connector/README.md`

## Current intent

- Preserve the Odoo 15 localization tree as a clean vendor import.
- Use it as the fiscal/domain basis for a future `odoo_integration` service.
- Keep it isolated from `app/` until a JSON-RPC or webhook adapter is implemented.
