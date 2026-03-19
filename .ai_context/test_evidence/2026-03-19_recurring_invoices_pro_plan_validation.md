# Evidencia de validacion: facturas recurrentes empaquetadas en Pro

Fecha: 2026-03-19

## Backend

Comando:

```powershell
.\.venv312\Scripts\python.exe -m pytest tests\test_recurring_invoices.py -q
```

Resultado:

- `4 passed in 6.05s`

Incluye validacion de:

- alta y listado de programaciones
- generacion por vencimiento
- pausa/reanudacion
- bloqueo del plan basico

## Frontend

Comandos:

```powershell
$env:Path='C:\Program Files\nodejs;'+$env:Path
& 'C:\Program Files\nodejs\corepack.cmd' pnpm --filter @getupsoft/client-portal build
& 'C:\Program Files\nodejs\corepack.cmd' pnpm --filter @getupsoft/admin-portal build
```

Resultado:

- `@getupsoft/client-portal build`: `OK`
- `@getupsoft/admin-portal build`: `OK`

Nota:

- Se mantiene la advertencia conocida de `runtime-config.js` en `index.html`, pero no bloquea el build.
