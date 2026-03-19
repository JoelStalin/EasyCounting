# Evidencia de validacion master plan

Fecha de ejecucion: 2026-03-19

## Backend

Comando:

```powershell
.\.venv312\Scripts\python -m pytest tests\test_email_service.py tests\test_auth_social_and_tours.py tests\test_client_onboarding.py tests\test_ri_router.py tests\test_partner_portal.py tests\test_admin_ai_providers.py tests\test_client_chat.py -q
```

Resultado:

- `20 passed in 9.38s`

Cobertura validada:

- servicio SMTP
- social auth y tickets de login
- MFA challenge-based
- persistencia de tours
- onboarding preliminar de tenant cliente
- RI real
- seller portal y permisos partner
- AI providers admin
- chatbot tenant-scoped

## Selenium Chrome

Comando:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\automation\run_selenium_live.ps1 -Browser chrome -SlowMoMs 150 -KeepOpenMs 500 -AdminBaseUrl http://127.0.0.1:18081 -ClientBaseUrl http://127.0.0.1:18082 -SellerBaseUrl http://127.0.0.1:18084 -CorporateBaseUrl http://127.0.0.1:18085 -ApiBaseUrl http://127.0.0.1:28080
```

Resultado:

- `5 passed in 94.54s`

Artefactos:

- `e2e/artifacts/live_20260319_133322/report.html`

Cobertura:

- admin login y companias
- client login, emision demo, perfil, logout
- seller login, emision demo, clientes, perfil, logout
- seller auditor sin permiso de emision
- sitio corporativo y producto `Accounting Management`
- tours autoguiados y relanzamiento por boton

## Selenium Edge

Comando:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\automation\run_selenium_live.ps1 -Browser edge -SlowMoMs 150 -KeepOpenMs 500 -AdminBaseUrl http://127.0.0.1:18081 -ClientBaseUrl http://127.0.0.1:18082 -SellerBaseUrl http://127.0.0.1:18084 -CorporateBaseUrl http://127.0.0.1:18085 -ApiBaseUrl http://127.0.0.1:28080
```

Resultado:

- `5 passed in 92.31s`

Artefactos:

- `e2e/artifacts/live_20260319_133540/report.html`

## Salud de servicios

Validacion HTTP:

- `http://127.0.0.1:28080/healthz` -> `200`
- `http://127.0.0.1:18081/login` -> `200`
- `http://127.0.0.1:18082/login` -> `200`
- `http://127.0.0.1:18084/login` -> `200`
- `http://127.0.0.1:18085/` -> `200`
- `http://127.0.0.1:19069/web/login` -> `200`

## Odoo 19 lab

Estado mantenido del laboratorio:

- login disponible en `http://127.0.0.1:19069/web/login`
- factura de prueba previamente posteada
- generacion base de reporte DGII previamente validada

La fase actual no reabre certificacion fiscal; mantiene el smoke tecnico del laboratorio como baseline valido.
