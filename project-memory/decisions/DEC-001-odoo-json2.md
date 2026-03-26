# DEC-001 Odoo 19 via JSON-2

- Fecha: 2026-03-25
- Tema: transporte de integración Odoo 19
- Fuente:
  - https://www.odoo.com/documentation/19.0/developer/reference/external_rpc_api.html
  - https://www.odoo.com/documentation/19.0/applications/finance/accounting.html
- Conclusión práctica:
  - Se adopta JSON-2 como transporte objetivo y no XML-RPC/JSON-RPC legacy.
  - El sync contable se implementa en `app/infrastructure/odoo/json2_client.py` y `app/application/accounting_sync.py`.
- Archivos afectados:
  - `app/infrastructure/odoo/json2_client.py`
  - `app/infrastructure/odoo/mappers.py`
  - `app/application/accounting_sync.py`
- Impacto:
  - Alineación con Odoo 19 y desacople del bridge contable.
