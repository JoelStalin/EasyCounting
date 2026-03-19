# neo_do_localization for dgii_encf

Este arbol contiene una copia del paquete `neo_do_localization` extraido desde el ambiente SSH `jabiya` y colocado en este repositorio como asset de integracion Odoo.

Origen:

- Host SSH: `jabiya`
- Ruta remota: `/opt/odoo-docker/addons/neo_do_localization`
- Commit remoto base: `64708451b8d64173c52c222f66dfb39ef9abfae2`
- Fecha de copia: `2026-03-18`

Modulos incluidos:

- `l10n_do_accounting`
- `l10n_do_accounting_report`
- `l10n_do_e_accounting`
- `l10n_do_pos`
- `l10n_do_rnc_search`

Adaptacion a este proyecto:

- El arbol se guarda bajo `integration/odoo/` para no mezclar addons Odoo con `app/`.
- Se removio la metadata Git anidada (`.git`) del origen remoto.
- Se limpiaron directorios `__pycache__`.
- Se agregaron archivos de mapeo y metadata local para conectar este paquete con el futuro `odoo_integration` del proyecto.

Uso previsto:

- referencia funcional para sincronizacion Odoo <-> dgii_encf
- base para un microservicio `odoo_integration` desacoplado
- mapeo de `account.move` y `res.company` con los modelos `Invoice` y `Tenant`

Archivos locales agregados:

- `SOURCE_METADATA.md`
- `GETUPSOFT_MAPPING.md`
- `getupsoft_connector/README.md`
