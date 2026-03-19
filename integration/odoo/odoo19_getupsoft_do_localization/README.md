# odoo19_getupsoft_do_localization for dgii_encf

Este arbol contiene una variante local `GetUpSoft` del paquete Odoo importado desde `jabiya`, preparada como asset de integracion para `dgii_encf` y versionada hacia `Odoo 19.0`.

Origen:

- Host SSH: `jabiya`
- Ruta remota original: `/opt/odoo-docker/addons/neo_do_localization`
- Commit remoto base: `64708451b8d64173c52c222f66dfb39ef9abfae2`
- Fecha de copia: `2026-03-18`
- Adaptacion local: renombre de modulos y metadatos a prefijo `getupsoft_*`

Modulos incluidos:

- `getupsoft_l10n_do_accounting`
- `getupsoft_l10n_do_accounting_report`
- `getupsoft_l10n_do_e_accounting`
- `getupsoft_l10n_do_pos` (pendiente de reescritura OWL para Odoo 19)
- `getupsoft_l10n_do_rnc_search`

Adaptacion a este proyecto:

- El arbol se guarda bajo `integration/odoo/` para no mezclar addons Odoo con `app/`.
- Se removio la metadata Git anidada (`.git`) del origen remoto.
- Se limpiaron directorios `__pycache__`.
- Se renombraron manifests, hooks, assets e IDs visibles para consolidar la marca `GetUpSoft`.
- Se migraron vistas XML desde `attrs` heredado hacia expresiones directas compatibles con Odoo 19.
- Se actualizaron manifests y versiones a la serie `19.0`.
- Se agregaron archivos de mapeo y metadata local para conectar este paquete con el futuro `odoo_integration` del proyecto.

Uso previsto:

- referencia funcional para sincronizacion Odoo <-> dgii_encf
- base para un microservicio `odoo_integration` desacoplado
- mapeo de `account.move` y `res.company` con los modelos `Invoice` y `Tenant`

Archivos locales agregados:

- `SOURCE_METADATA.md`
- `GETUPSOFT_MAPPING.md`
- `getupsoft_connector/README.md`
