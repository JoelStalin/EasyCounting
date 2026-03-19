# Source Metadata

Snapshot local obtenido desde el ambiente `jabiya`.

Fuente remota:

- host: `jabiya`
- ruta: `/opt/odoo-docker/addons/neo_do_localization`
- commit: `64708451b8d64173c52c222f66dfb39ef9abfae2`

Estado del working tree remoto al momento de copiar:

- modificado: `l10n_do_accounting/models/account_move.py`
- modificado: `l10n_do_e_accounting/__manifest__.py`
- modificado: `l10n_do_e_accounting/models/__init__.py`
- nuevo: `l10n_do_e_accounting/models/account_move.py`
- nuevo: `l10n_do_e_accounting/models/res_company.py`
- nuevo: `l10n_do_e_accounting/views/`

Notas:

- La copia local preserva esos cambios del working tree activo porque parecen formar parte del estado realmente desplegado en `jabiya`.
- No se importo el `.git` remoto para evitar un repositorio anidado dentro de `dgii_encf`.
