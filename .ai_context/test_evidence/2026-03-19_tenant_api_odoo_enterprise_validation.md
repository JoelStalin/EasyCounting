# 2026-03-19 - Validacion API empresarial Odoo

## Pruebas backend

Comando:

```powershell
.\.venv312\Scripts\python.exe -m pytest tests\test_tenant_api_tokens.py tests\test_client_onboarding.py -q
```

Resultado:

- `5 passed in 20.15s`

Cobertura validada:

- creacion de token API por tenant
- listado y revocacion
- lectura de facturas por bearer token empresarial
- registro de factura por token `read_write`
- rechazo de token `read`
- rechazo por onboarding fiscal pendiente

## Build frontend

Comando:

```powershell
$env:Path='C:\Program Files\nodejs;'+$env:Path
& 'C:\Program Files\nodejs\corepack.cmd' pnpm --filter @getupsoft/client-portal build
```

Resultado:

- build `OK`
- `vite` genero `dist/`
- advertencia no bloqueante ya existente por `runtime-config.js` sin `type="module"` en `index.html`
