# Odoo 15 GetUpSoft lab and credentials

Fecha: 2026-03-19

## Renombre de assets Odoo en este repo

- `integration/odoo/neo_do_localization` -> `integration/odoo/odoo15_getupsoft_do_localization`
- `integration/odoo/getupsoft_do_localization` -> `integration/odoo/odoo19_getupsoft_do_localization`

## Credenciales de portales dgii_encf

- Admin portal:
  - URL: `http://127.0.0.1:18081/login`
  - user: `admin@getupsoft.com.do`
  - password: `ChangeMe123!`
- Client portal:
  - URL: `http://127.0.0.1:18082/login`
  - user: `cliente@getupsoft.com.do`
  - password: `Tenant123!`
- Seller portal:
  - URL: `http://127.0.0.1:18084/login`
  - user: `seller@getupsoft.com.do`
  - password: `Seller123!`
- Seller auditor:
  - URL: `http://127.0.0.1:18084/login`
  - user: `seller.auditor@getupsoft.com.do`
  - password: `SellerAudit123!`

## Odoo 19 lab

- URL: `http://127.0.0.1:19069/web/login`
- Admin web:
  - login: `admin`
  - password: `admin`
- PostgreSQL host port: `55439`
- db user: `odoo`
- db password: `odoo`

Nota:

- El lab Odoo 19 ya estaba operativo previamente.
- Esta fase no redefinio usuarios funcionales nuevos dentro de ese lab; se confirmo solo el acceso administrativo existente.

## Odoo 15 copy: getupsoft

Ruta:

- `C:\Users\yoeli\Documents\jabiya15\odoo15_getupsoft`

Estado:

- `db` healthy
- `odoo` healthy
- login HTTP `200` en `http://127.0.0.1:15069/web/login`

Credenciales:

- Master password: `GetupsoftMaster15!`
- Admin web:
  - login: `admin`
  - password: `GetupsoftAdmin15!`
- Functional user:
  - login: `qa.getupsoft15@example.com`
  - password: `GetupsoftQA15!`

Database:

- db name: `GetupsoftOdoo15Lab`
- db user: `odoo-v15-getupsoft`
- db password: `GetupsoftDb15!`
- host port: `15415`

Addons path activo:

- `/mnt/extra-addons/external/enterprise`
- `/mnt/extra-addons/jabiya`
- `/mnt/extra-addons/getupsoft_do_localization`
- `/mnt/extra-addons/external/extra`

Modulos del paquete fiscal en Odoo 15:

- `l10n_do_accounting` -> `installed`
- `l10n_do_accounting_report` -> `installed`
- `l10n_do_e_accounting` -> `installed`
- `l10n_do_rnc_search` -> `installed`
- `l10n_do_pos` -> `uninstalled`
