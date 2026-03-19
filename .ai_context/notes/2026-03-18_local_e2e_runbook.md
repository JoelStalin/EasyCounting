# Local E2E Runbook - 2026-03-18

## Command

```powershell
.venv\Scripts\python -m pytest e2e
```

## What the suite does

- Starts a local mock API on `http://localhost:8000`.
- Starts local SPA static servers for `frontend/apps/admin-portal/dist` and `frontend/apps/client-portal/dist` on free localhost ports.
- Runs Selenium against those portals.
- Stores failure screenshots under `e2e/artifacts/`.

## Environment knobs

- `HEADLESS=1` keeps browser headless. Set `HEADLESS=0` for visible runs.
- `ARTIFACTS_DIR=<path>` overrides where screenshots and logs are written.

## Constraint

- The compiled portal bundles currently point to `http://localhost:8000` as API base URL, so the mock API must stay on that port unless the bundles are rebuilt.

## Current covered flows

- Admin portal:
  - redirect to login
  - login
  - tenant list fetch
  - create tenant
  - open tenant detail
- Client portal:
  - redirect to login
  - login
  - submit e-CF UI form
  - open profile
  - logout
