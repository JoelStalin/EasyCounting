# Repo Audit - 2026-03-18

## Workspace summary

- Workspace root: `C:\Users\yoeli\Documents\dgii_encf`
- Git metadata: present; worktree is dirty with backend, infra and test changes outside this task
- Main stack: FastAPI backend, PostgreSQL/Redis infra, React + Vite admin/client portals, Selenium `e2e/`
- Existing E2E state before this session: placeholder smoke tests and one login example without selectors

## Runtime surfaces relevant to Selenium

- Admin portal source: `frontend/apps/admin-portal`
- Client portal source: `frontend/apps/client-portal`
- Shared frontend auth storage:
  - admin: `sessionStorage["getupsoft-admin-auth"]`
  - client: `sessionStorage["getupsoft-client-auth"]`
- Frontend API base URL default: `http://localhost:8000`, overridable with `VITE_API_BASE_URL`

## QA constraints detected

- The frontend depends on live API responses for login and some list/detail views.
- The existing backend supports portal auth, but local E2E should not depend on DB/Redis/container bootstrap for every run.
- A deterministic local mock API is the shortest path to stable Selenium coverage in this repo.

## Outcome of this session

- `.ai_context` bootstrapped for this project.
- `e2e/` upgraded to serve both compiled portal bundles from `dist/` and hit a local mock API on `http://localhost:8000`.
- Functional Selenium flows now cover redirect-to-login, successful auth, protected navigation, admin company creation, client e-CF submit simulation, and logout.
