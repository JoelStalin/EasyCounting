# API Odoo para clientes empresariales

Esta integracion permite que un cliente empresarial conecte su ERP Odoo al tenant correspondiente usando un token API aislado por empresa.

## Flujo operativo

1. Entrar al portal cliente.
2. Ir a `API Odoo`.
3. Generar un token con acceso:
   - `Solo lectura` para consultar facturas
   - `Lectura y registro` para consultar y registrar comprobantes
4. Copiar el token y guardarlo en Odoo.
5. Configurar la base URL y los endpoints empresariales.

## Endpoints

Base URL productiva esperada:

```text
https://api.getupsoft.com.do
```

Base URL local de laboratorio:

```text
http://127.0.0.1:28080
```

Endpoints:

```text
GET  /api/v1/tenant-api/invoices
GET  /api/v1/tenant-api/invoices/{invoice_id}
POST /api/v1/tenant-api/invoices
```

Autenticacion:

```text
Authorization: Bearer <TOKEN_EMPRESARIAL>
```

## Ejemplo de consulta

```bash
curl "https://api.getupsoft.com.do/api/v1/tenant-api/invoices?page=1&size=20" \
  -H "Authorization: Bearer <TOKEN_EMPRESARIAL>"
```

## Ejemplo de registro

```bash
curl -X POST "https://api.getupsoft.com.do/api/v1/tenant-api/invoices" \
  -H "Authorization: Bearer <TOKEN_EMPRESARIAL>" \
  -H "Content-Type: application/json" \
  -d '{
    "encf": "E310000000123",
    "tipoEcf": "E31",
    "rncReceptor": "131415161",
    "total": "1500.00"
  }'
```

## Reglas importantes

- El token solo accede al tenant que lo emitio.
- Un token revocado deja de funcionar de inmediato.
- Los tenants en `pending_fiscal_setup` no pueden registrar facturas reales por API.
- Un token `read` no puede usar `POST /tenant-api/invoices`.
- El portal cliente sigue siendo la fuente para revisar rapidamente el estado de los comprobantes del mismo tenant.
