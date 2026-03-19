# 2026-03-19 - Validacion de facturas recurrentes

## Pruebas backend

Comando:

```powershell
.\.venv312\Scripts\python.exe -m pytest tests\test_recurring_invoices.py tests\test_tenant_api_tokens.py tests\test_client_onboarding.py -q
```

Resultado:

- `8 passed in 8.08s`

Cobertura:

- crear y listar programaciones recurrentes
- ejecutar vencidas y materializar `Invoice`
- pausar y reanudar
- validacion previa de onboarding
- sin regresion en API empresarial Odoo y onboarding cliente

## Build frontend

Comando:

```powershell
$env:Path='C:\Program Files\nodejs;'+$env:Path
& 'C:\Program Files\nodejs\corepack.cmd' pnpm --filter @getupsoft/client-portal build
```

Resultado:

- build `OK`
- advertencia no bloqueante ya existente por `runtime-config.js` en `index.html`
