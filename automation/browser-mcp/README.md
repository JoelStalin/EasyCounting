# Browser MCP Sidecar

Servicio Node.js/TypeScript para automatización de navegador con dos interfaces:

1. `stdio` usando `@playwright/mcp` oficial para clientes MCP locales.
2. HTTP con:
   - proxy `/mcp` al servidor oficial Playwright MCP
   - API `/api/v1/jobs/*` para escenarios reutilizables consumidos por backend y jobs

## Arquitectura

```text
Agents / MCP clients
  -> stdio (`npm run mcp:stdio`) OR HTTP `/mcp`
      -> @playwright/mcp oficial

Backend / jobs / FastAPI
  -> HTTP `/api/v1/jobs/run-sync`
      -> JobRunner
      -> Browser runtime (Playwright)
      -> Scenario registry
      -> Artifacts / sessions / logs
```

## Carpetas

- `src/config`: carga y validación de configuración.
- `src/runtime`: lifecycle del browser/context/page.
- `src/services`: artifacts, sesiones, network policy, runner y logging.
- `src/scenarios`: escenarios reutilizables.
- `src/launch`: entrypoints `stdio` y `http`.
- `tests`: smoke tests del sidecar.

## Decisiones

- `@playwright/mcp` es la base MCP para no reinventar el protocolo.
- El API de jobs vive aparte porque los escenarios de negocio necesitan contratos estables y evidencia consistente.
- `persistent_profile`, `isolated_session` y `cdp_attach` están diferenciados para no mezclar sesiones por accidente.
- Los artifacts se guardan por job en directorios determinísticos.

## Configuración

Archivo JSON base: `config/browser-mcp.config.json`

Variables relevantes:

- `BROWSER_MCP_SERVICE_HOST`
- `BROWSER_MCP_SERVICE_PORT`
- `BROWSER_MCP_DEFAULT_BROWSER`
- `BROWSER_MCP_CHROMIUM_CHANNEL`
- `BROWSER_MCP_DEFAULT_HEADLESS`
- `BROWSER_MCP_OUTPUT_ROOT`
- `BROWSER_MCP_SESSIONS_ROOT`
- `BROWSER_MCP_ALLOWED_ORIGINS`
- `BROWSER_MCP_BLOCKED_ORIGINS`
- `BROWSER_MCP_ACTION_TIMEOUT_MS`
- `BROWSER_MCP_NAVIGATION_TIMEOUT_MS`
- `BROWSER_MCP_TRACE_DEFAULT`
- `BROWSER_MCP_SAVE_SESSION_DEFAULT`

## Comandos

```bash
npm install
npm run browsers:install
npm run build
npm run lint
npm run test
```

### MCP local por stdio

```bash
npm run mcp:stdio
```

Ejemplo para un cliente MCP:

```json
{
  "mcpServers": {
    "playwright-getupsoft": {
      "command": "npm",
      "args": ["--prefix", "automation/browser-mcp", "run", "mcp:stdio"]
    }
  }
}
```

### Servicio HTTP

```bash
npm run mcp:http
```

Endpoints:

- `GET /healthz`
- `POST /api/v1/jobs`
- `POST /api/v1/jobs/run-sync`
- `GET /api/v1/jobs/:jobId`
- `GET /api/v1/jobs/:jobId/runtime`
- `DELETE /api/v1/jobs/:jobId/runtime`
- `GET /api/v1/jobs/:jobId/events`
- `GET /api/v1/sessions`
- `DELETE /api/v1/sessions/:sessionRef`
- `ALL /mcp`

## Ejemplos de escenarios

- `open-url-extract`
- `login-persistent-session`
- `form-fill`
- `download-evidence`
- `cookies-localstorage`
- `network-intercept`
- `pdf-screenshot`
- `multi-tab`
- `dgii-ofv-login`
- `dgii-postulacion-open`
- `dgii-postulacion-generate-xml`
- `dgii-postulacion-upload-signed-xml`
- `odoo-login`

## Ejemplo de job

```json
{
  "jobId": "smoke-001",
  "scenario": "open-url-extract",
  "target": {
    "url": "https://example.com"
  },
  "mode": "isolated_session",
  "keepOpenOnFailure": false,
  "artifacts": {
    "screenshot": true,
    "snapshot": true,
    "trace": false
  }
}
```

## Sesion abierta al fallar

- `keepOpenOnFailure=true` solo es util en `persistent_profile` y con `headless=false`.
- El runner conserva la ventana abierta para inspeccion manual y expone `GET /api/v1/jobs/:jobId/runtime`.
- Para liberar ese navegador retenido: `DELETE /api/v1/jobs/:jobId/runtime`.
- Si el navegador queda abierto, ese `userDataDir` puede quedar bloqueado hasta liberar o cerrar la ventana.

## Baseline DGII repetible

- Perfil fuente real: `Default / JOEL STALIN`.
- El flujo DGII nunca automatiza sobre el perfil vivo; clona el perfil a un directorio de trabajo exclusivo.
- Para correr sobre Chrome estable y maximizar compatibilidad con el perfil real, usa `BROWSER_MCP_CHROMIUM_CHANNEL=chrome`.
- La secuencia canonica y su clasificacion viven en:
  - `docs/certificados/autoasistido/dgii_postulacion_test_manifest.json`
  - `docs/certificados/autoasistido/latest_known_state.json`
  - `docs/certificados/autoasistido/run_notes/`
- Warnings `Feature-Policy/Permissions-Policy` se registran como `warning_non_blocking` salvo evidencia funcional.

## Docker

```bash
docker compose up -d browser-mcp
docker compose logs -f browser-mcp
```

## Límites reales del sistema

- Esto no es un bypass de seguridad.
- No elimina CAPTCHA, anti-bot, SSO, CORS ni políticas del sitio.
- Los perfiles persistentes reducen fricción operativa, pero exigen higiene de secretos y aislamiento por tenant/job.
- Los escenarios DGII/Odoo reales deben ejecutarse como suites controladas y no como parte del CI por defecto.
