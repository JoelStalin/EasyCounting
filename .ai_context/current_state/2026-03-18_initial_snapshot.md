# Initial Snapshot - 2026-03-18

## Local workspace

- Workspace root: `C:\Users\yoeli\Documents\dgii_encf`
- Main backend entrypoint: `app/main.py`
- Frontend workspace root: `frontend/`
- Frontend apps:
  - `frontend/apps/admin-portal`
  - `frontend/apps/client-portal`
- Existing E2E directory: `e2e/`

## Architecture relevant to UI functional testing

- Backend: FastAPI with portal auth under `/auth/*` and versioned routes under `/api/v1/*`
- Frontend: React 18 + Vite + Zustand + React Query
- Auth model:
  - platform users navigate admin portal with scope `PLATFORM`
  - tenant users navigate client portal with scope `TENANT`
- Protected routes redirect unauthenticated users to `/login`

## Selenium execution model adopted

- Start a lightweight mock API in-process for deterministic portal auth and admin tenant CRUD.
- Start both compiled portal bundles from `frontend/apps/*/dist` using local SPA static servers.
- Run Selenium against the real React apps, not static screenshots or mocked DOM fragments.
- Capture screenshots in `e2e/artifacts/` on failure.

## Known local prerequisites

- compiled frontend bundles already present under `frontend/apps/admin-portal/dist` and `frontend/apps/client-portal/dist`
- Selenium-compatible browser available locally through Chrome or Edge
