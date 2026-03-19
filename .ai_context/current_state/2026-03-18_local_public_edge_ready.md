# 2026-03-18 - Local public edge ready

## Status

- Frontend build local restored with `Node 24.14.0` and `pnpm 9.15.9`.
- Admin and client `dist` rebuilt successfully.
- Local origin stable on:
  - `http://127.0.0.1:28080` -> backend/nginx
  - `http://127.0.0.1:18081` -> admin SPA
  - `http://127.0.0.1:18082` -> client SPA
  - `http://127.0.0.1:18083` -> apex redirect shim
- Docker Desktop was started and the compose stack is currently up with `deploy/docker-compose.wsl-local.yml`.
- Real demo data was seeded in the running database:
  - `admin@getupsoft.com.do` / `ChangeMe123!` with role `platform_superroot`
  - `cliente@getupsoft.com.do` / `Tenant123!` with role `tenant_user`
  - `Empresa Demo` tenant plus sample invoice/usage/ledger rows

## Important fixes made

- Removed local host-port exposure for `db` and `redis`; they remain internal to compose.
- Moved local backend edge from `18080` to `28080` because `127.0.0.1:18080` is occupied on this machine by `wslrelay.exe`.
- Fixed runtime API resolution so SPAs honor `runtime-config.js` at request time instead of freezing the API base URL during module import.
- Fixed real-login breakage caused by invalid `.local` emails; defaults, seeding and Selenium now use `@getupsoft.com.do`.
- Fixed local CORS in `.env` for `127.0.0.1:18081/18082/18083`.
- Fixed Selenium harness for external/local-real URLs and removed ID/RNC assumptions that were making the smoke brittle across repeated runs and browsers.

## Cloudflare readiness

- `cloudflared` installed on Windows at `C:\Program Files (x86)\cloudflared\cloudflared.exe`
- New automation entrypoint: `scripts/automation/configure_cloudflare_public_edge.ps1`
- Quick tunnel helper updated: `scripts/automation/start_cloudflared_quick_tunnel.ps1`
- Manual template remains in `ops/cloudflared/getupsoft.com.do.example.yml`

## Current blocker

Public publication to `https://api.getupsoft.com.do`, `https://admin.getupsoft.com.do`, `https://cliente.getupsoft.com.do` is blocked only by missing Cloudflare API credentials.

To execute the live Cloudflare cutover, the next run needs:

- `CLOUDFLARE_API_TOKEN`
- `CLOUDFLARE_ACCOUNT_ID` if the zone must be created or if the account cannot be inferred from an existing zone

Minimum token scopes for the automation:

- `Account -> Cloudflare Tunnel -> Edit`
- `Zone -> DNS -> Edit`
- `Zone -> Single Redirect -> Edit`
- `Zone -> Zone -> Edit` only if the zone does not already exist and should be created by script
