# GetUpSoft Localization Refactor

Fecha: `2026-03-18`

## Alcance

Se creo una variante local `integration/odoo/getupsoft_do_localization` a partir del snapshot remoto `neo_do_localization` traido desde `jabiya`.

Cambios aplicados:

- renombre de modulos Odoo a prefijo `getupsoft_*`
- ajuste de manifests, hooks y nombres visibles a branding `GetUpSoft`
- saneamiento del modulo `getupsoft_l10n_do_rnc_search`
- correccion de assets rotos causados por el renombre masivo
- actualizacion de metadata y documentacion de integracion hacia `Tenant` e `Invoice`

## Validaciones

- `python -m compileall integration/odoo/getupsoft_do_localization` -> `OK`
- verificacion estructural de `__manifest__.py` y existencia de archivos declarados en `data` y `assets` -> `OK`
- busqueda de residuos `AstraTech`, `Neotec`, `getupsoft_getupsoft` y `astra_*` dentro de `integration/odoo/getupsoft_do_localization` -> sin hallazgos funcionales

## Nota

El arbol queda preparado como asset de integracion Odoo dentro de este repositorio. Todavia no existe un `odoo_integration` ejecutable dentro del backend FastAPI para sincronizacion activa con una instancia Odoo.
