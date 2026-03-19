# Odoo 19 Versioning

Fecha: `2026-03-18`

## Resultado

La variante `integration/odoo/getupsoft_do_localization` fue elevada a la serie `Odoo 19.0`.

## Cambios aplicados

- manifests actualizados a `19.0.1.0.0`
- migracion de vistas XML desde `attrs` heredado a atributos directos compatibles con Odoo 19
- actualizacion de metadata `Project-Id-Version` en archivos `po`
- ajuste del bundle POS a `point_of_sale._assets_pos`
- documentacion de estado de migracion en `ODOO19_MIGRATION.md`

## Validaciones

- `python -m compileall integration/odoo/getupsoft_do_localization` -> `OK`
- validacion de `__manifest__.py` y resolucion de archivos `data/assets` -> `OK`
- barrido de `attrs=` y `<attribute name="attrs">` remanentes -> sin hallazgos

## Riesgo aceptado

`getupsoft_l10n_do_pos` no fue marcado como instalable en Odoo 19 porque su frontend POS depende de APIs legacy de Odoo 15 y requiere una reescritura OWL para ser funcional.
