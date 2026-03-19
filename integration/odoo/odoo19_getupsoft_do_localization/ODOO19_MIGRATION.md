# Odoo 19 Migration Notes

Estado del paquete `getupsoft_do_localization` despues de la elevacion a `Odoo 19.0`.

## Migrado

- manifests y versiones a serie `19.0`
- vistas XML con `attrs` migradas a expresiones directas `invisible`, `readonly` y `required`
- bundle POS actualizado a `point_of_sale._assets_pos`
- metadata e i18n ajustadas a objetivo `Odoo 19`
- autocomplete y validacion RNC redirigidos a servicios locales de `dgii_encf`

## Operativo

- `getupsoft_l10n_do_accounting`
- `getupsoft_l10n_do_accounting_report`
- `getupsoft_l10n_do_e_accounting`
- `getupsoft_l10n_do_rnc_search`

## Pendiente

- `getupsoft_l10n_do_pos`

Motivo:

- la capa POS de Odoo 19 usa la estructura moderna `@point_of_sale/app/...`
- el addon heredado desde Odoo 15 extiende clases legacy como `point_of_sale.PaymentScreen`, `point_of_sale.Registries` y `point_of_sale.models`
- esa parte requiere una reescritura OWL real, no solo un bump de manifest

Decision aplicada:

- el modulo POS queda en el arbol con manifiesto `19.0`
- `installable` queda en `False` para evitar una instalacion falsa o rota en Odoo 19
