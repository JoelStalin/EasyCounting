# Selenium Live Rerun - Admin and Client - 2026-03-18

## Command

```powershell
powershell -ExecutionPolicy Bypass -File scripts\automation\run_selenium_live.ps1 -Browser chrome -SlowMoMs 1200 -KeepOpenMs 12000
```

## Result

- `2 passed in 78.93s`
- HTML report generated at:
  - `e2e/artifacts/live_20260318_174619/report.html`

## Visual evidence

- `e2e/artifacts/live_20260318_174619/01_admin_redirect_to_login.png`
- `e2e/artifacts/live_20260318_174619/03_admin_companies_loaded.png`
- `e2e/artifacts/live_20260318_174619/05_admin_company_created.png`
- `e2e/artifacts/live_20260318_174619/06_admin_company_detail_open.png`
- `e2e/artifacts/live_20260318_174619/01_client_redirect_to_login.png`
- `e2e/artifacts/live_20260318_174619/05_client_emit_success.png`
- `e2e/artifacts/live_20260318_174619/06_client_profile_open.png`

## Scope covered in this visual rerun

- Admin portal:
  - redirect to login
  - login
  - companies list
  - create company
  - open company detail
- Client portal:
  - redirect to login
  - login
  - emit e-CF simulated flow
  - profile view
  - logout

## Limitation

The new `Agentes IA` page exists in source:

- `frontend/apps/admin-portal/src/pages/AIProviders.tsx`

but it was not included in this Selenium rerun because the current admin `dist` bundle was not rebuilt successfully on this workstation. The frontend workspace has a partially repaired Node/pnpm environment, but `tsc/vite` resolution is still inconsistent in this host.

The backend for the feature is already verified separately through:

- `tests/test_admin_ai_providers.py`
- `tests/test_client_chat.py`

and the runtime integration is implemented in:

- `app/application/tenant_chat.py`
- `app/routers/admin.py`
