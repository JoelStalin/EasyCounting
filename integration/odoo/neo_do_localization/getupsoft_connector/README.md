# getupsoft_connector placeholder

Este directorio queda reservado para el codigo adaptador entre `dgii_encf` y Odoo usando `neo_do_localization`.

Responsabilidades esperadas:

- traducir `Tenant` -> `res.company`
- traducir `Invoice` -> `account.move`
- resolver fiscal positions y tipos documentales dominicanos
- exponer sync jobs o webhooks para el futuro servicio `odoo_integration`

Implementacion sugerida:

- cliente JSON-RPC Odoo
- mapping de campos por modulo
- reconciliacion de estado contable Odoo -> `Invoice.contabilizado`
