# 2026-03-19 - API empresarial Odoo para portal cliente

## Objetivo

Permitir que un cliente empresarial conecte su ERP Odoo por API, genere sus propios tokens desde el portal cliente y revise sus comprobantes dentro del mismo tenant.

## Backend entregado

- Tabla nueva `tenant_api_tokens`.
- Servicio `TenantApiService` para:
  - crear/listar/revocar tokens
  - autenticar tokens con scopes
  - listar facturas por tenant
  - consultar detalle de factura
  - registrar facturas por API empresarial
- Router cliente:
  - `GET /api/v1/cliente/api-tokens`
  - `POST /api/v1/cliente/api-tokens`
  - `DELETE /api/v1/cliente/api-tokens/{token_id}`
- Router empresarial:
  - `GET /api/v1/tenant-api/invoices`
  - `GET /api/v1/tenant-api/invoices/{invoice_id}`
  - `POST /api/v1/tenant-api/invoices`
- Validacion de base64 para `xmlSignedBase64`.
- Bloqueo de registro por API cuando `tenant.onboarding_status != completed`.
- Nuevo permiso tenant: `TENANT_API_TOKEN_MANAGE`.

## Frontend entregado

- Nueva seccion en portal cliente:
  - ruta `integrations/odoo`
  - navegable como `API Odoo`
- La vista permite:
  - generar tokens por integracion
  - revocar tokens activos
  - copiar el token generado una sola vez
  - ver base URL y endpoints para Odoo
  - ver ejemplo `curl`
  - revisar ultimos comprobantes del tenant
- Tour autoguiado agregado para la vista `client-odoo-api`.

## Documentacion

- Guia nueva: `docs/guide/20-odoo-api-cliente-empresarial.md`
- README de conectores Odoo actualizado para Odoo 15 y Odoo 19.
