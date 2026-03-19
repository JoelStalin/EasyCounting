# Evidencia de Pruebas Reales y Validacion Publica HTTP - 2026-03-18

## Pruebas funcionales reales cerradas

Se ejecuto Selenium contra backend real, no contra el mock, usando arneses same-origin locales:

### Chrome

Comando:

```powershell
ADMIN_BASE_URL=http://127.0.0.1:18181
CLIENT_BASE_URL=http://127.0.0.1:18182
API_BASE_URL=http://127.0.0.1:28080
BROWSER=chrome
HEADLESS=1
python -m pytest e2e/tests -q --html=e2e/artifacts/local_real_backend_chrome_20260318_2232/report.html --self-contained-html
```

Resultado:

- `2 passed`

Artefactos:

- `e2e/artifacts/local_real_backend_chrome_20260318_2232/report.html`
- screenshots por paso dentro del mismo directorio

### Edge

Comando:

```powershell
ADMIN_BASE_URL=http://127.0.0.1:18181
CLIENT_BASE_URL=http://127.0.0.1:18182
API_BASE_URL=http://127.0.0.1:28080
BROWSER=edge
HEADLESS=1
python -m pytest e2e/tests -q --html=e2e/artifacts/local_real_backend_edge_20260318_2232/report.html --self-contained-html
```

Resultado:

- `2 passed`

Artefactos:

- `e2e/artifacts/local_real_backend_edge_20260318_2232/report.html`
- screenshots por paso dentro del mismo directorio

## Cobertura funcional validada

### Admin

- redirect a login
- autenticacion real
- carga de companias
- vista `Agentes IA`
- creacion de compania
- apertura de detalle de compania

### Cliente

- redirect a login
- autenticacion real
- acceso a emision e-CF
- carga del formulario
- envio simulado
- acceso a perfil
- logout

## Validacion publica HTTP

Se comprobo por `curl` contra el edge publico:

- `http://api.getupsoft.com.do/healthz` -> `200`
- `http://admin.getupsoft.com.do/login` -> `200`
- `http://cliente.getupsoft.com.do/login` -> `200`
- `http://getupsoft.com.do/` -> `301` a `http://admin.getupsoft.com.do/`

## Diagnosticos adicionales cerrados

- `runtime-config.js` publico ya entrega base correcta por host:
  - admin -> `http://admin.getupsoft.com.do`
  - cliente -> `http://cliente.getupsoft.com.do`
- login same-origin local en cliente contra `/api/v1/auth/login` da `200`
- login directo al backend en `127.0.0.1:28080/api/v1/auth/login` da `200`

## Bloqueos que permanecen fuera del alcance de la app

### Selenium directo a hostnames publicos

El WebDriver de Chrome/Edge sigue encontrando intermitentemente:

- `ERR_SSL_VERSION_OR_CIPHER_MISMATCH`

al navegar directamente a `http://admin.getupsoft.com.do` o `http://cliente.getupsoft.com.do`, aun cuando los endpoints HTTP responden por `curl`.

### Edge/WAF de Cloudflare

`POST` scripted no navegador a:

- `http://admin.getupsoft.com.do/api/v1/auth/login`
- `http://cliente.getupsoft.com.do/api/v1/auth/login`

devuelve:

- `403`
- `error code: 1010`

Por eso la evidencia Selenium estable se cerro sobre el arnes same-origin local conectado al backend real.

