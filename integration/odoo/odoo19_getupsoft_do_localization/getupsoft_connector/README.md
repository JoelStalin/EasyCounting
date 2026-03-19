# getupsoft_connector placeholder

Este directorio queda reservado para el codigo adaptador entre `dgii_encf` y Odoo usando `odoo19_getupsoft_do_localization`.

Responsabilidades esperadas:

- traducir `Tenant` -> `res.company`
- traducir `Invoice` -> `account.move`
- resolver fiscal positions y tipos documentales dominicanos
- exponer sync jobs o webhooks para el futuro servicio `odoo_integration`
- consumir el API empresarial por tenant con tokens emitidos desde el portal cliente

Implementacion sugerida:

- cliente JSON-RPC Odoo
- mapping de campos por modulo
- reconciliacion de estado contable Odoo -> `Invoice.contabilizado`
- lectura desde `/api/v1/admin/tenants`, `/api/v1/admin/invoices` y servicios internos del backend
- endpoints nuevos para contabilizacion si se decide evitar acceso directo a base de datos
- cliente HTTP para `GET/POST /api/v1/tenant-api/invoices`

Referencia operativa:

- portal cliente -> seccion `API Odoo`
- guia tecnica: `docs/guide/20-odoo-api-cliente-empresarial.md`
