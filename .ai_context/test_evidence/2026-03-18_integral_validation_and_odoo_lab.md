# Evidencia integral de validación

## Backend y RBAC

Comando:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_ri_router.py tests\test_partner_portal.py tests\test_admin_ai_providers.py tests\test_client_chat.py -q
```

Resultado:

- `10 passed in 7.29s`

Cobertura validada:

- RI real bajo la capa compat
- portal seller / reseller / auditor
- proveedores IA para `platform_superroot`
- chatbot tenant-scoped

## Selenium público

### Chrome

Comando:

```powershell
$env:ADMIN_BASE_URL='https://admin.getupsoft.com.do'
$env:CLIENT_BASE_URL='https://cliente.getupsoft.com.do'
$env:SELLER_BASE_URL='https://socios.getupsoft.com.do'
$env:API_BASE_URL='https://api.getupsoft.com.do'
$env:HEADLESS='1'
$env:BROWSER='chrome'
$env:ARTIFACTS_DIR='e2e/artifacts/public_chrome_20260318_integral'
.\.venv\Scripts\python.exe -m pytest e2e\tests\test_admin_smoke.py e2e\tests\test_client_smoke.py e2e\tests\test_seller_smoke.py -q
```

Resultado:

- `4 passed`

Artefactos:

- `e2e/artifacts/public_chrome_20260318_integral`

Pasos gráficos relevantes:

- `04_admin_ai_providers_open.png`
- `05_client_emit_success.png`
- `04_seller_emit_success.png`
- `05_seller_clients_open.png`
- `06_seller_profile_open.png`

### Edge

Comando:

```powershell
$env:ADMIN_BASE_URL='https://admin.getupsoft.com.do'
$env:CLIENT_BASE_URL='https://cliente.getupsoft.com.do'
$env:SELLER_BASE_URL='https://socios.getupsoft.com.do'
$env:API_BASE_URL='https://api.getupsoft.com.do'
$env:HEADLESS='1'
$env:BROWSER='edge'
$env:ARTIFACTS_DIR='e2e/artifacts/public_edge_20260318_integral'
.\.venv\Scripts\python.exe -m pytest e2e\tests\test_admin_smoke.py e2e\tests\test_client_smoke.py e2e\tests\test_seller_smoke.py -q
```

Resultado:

- `4 passed`

Artefactos:

- `e2e/artifacts/public_edge_20260318_integral`

## Laboratorio Odoo 19 con Chefalitas

Bootstrap limpio validado anteriormente con:

```powershell
docker compose -f labs\odoo19_chefalitas\docker-compose.yml exec -T db psql -U odoo -d postgres -c "drop database if exists chefalitas19lab with (force);"
powershell -ExecutionPolicy Bypass -File scripts\automation\odoo19_chefalitas\bootstrap_lab.ps1
```

Resultado funcional confirmado en base:

```json
{
  "invoice": {
    "id": 1,
    "name": "B01 00000001",
    "state": "posted",
    "document_number": "00000001",
    "partner": "Cliente Prueba Odoo 19",
    "amount_total": 2500.0
  },
  "report": {
    "id": 1,
    "name": "03/2026",
    "state": "generated",
    "sale_records": 1,
    "purchase_records": 0
  }
}
```

Consulta usada:

```powershell
@'
import json
invoice = env['account.move'].search([('move_type', '=', 'out_invoice')], order='id desc', limit=1)
report = env['dgii.reports'].search([], order='id desc', limit=1)
print(json.dumps({
  'invoice': {
    'id': invoice.id,
    'name': invoice.name,
    'state': invoice.state,
    'document_number': getattr(invoice, 'l10n_latam_document_number', None),
    'partner': invoice.partner_id.name,
    'amount_total': invoice.amount_total,
  },
  'report': {
    'id': report.id,
    'name': report.name,
    'state': report.state,
    'sale_records': getattr(report, 'sale_records', None),
    'purchase_records': getattr(report, 'purchase_records', None),
  },
}, ensure_ascii=True))
'@ | docker compose -f labs\odoo19_chefalitas\docker-compose.yml exec -T odoo odoo shell -c /etc/odoo/odoo.conf -d chefalitas19lab
```

## Logs corregidos en esta fase

- `Model attribute '_sql_constraints' is no longer supported` -> corregido en los dos modelos críticos del módulo DGII report.
- `missing --http-interface/http_interface` -> corregido en `labs/odoo19_chefalitas/odoo.conf`.
- `docker-compose.yml: the attribute version is obsolete` -> corregido en los compose del repo objetivo.

## Logs aún presentes pero fuera del baseline aceptado

- `jabiya15local-queue_consumer-1` sigue reiniciando por hostname `db`; se documenta como herencia externa y no bloquea el baseline `dgii_encf + demo + odoo19_chefalitas`.
