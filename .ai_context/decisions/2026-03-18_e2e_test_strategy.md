# Decision Log - 2026-03-18

## Decision

Use Selenium against real admin/client React portal bundles with a local mock API, instead of depending on the full FastAPI + DB + Redis stack for local functional smoke coverage.

## Reasoning

- The previous `e2e/` coverage was too weak to protect portal behavior.
- The portals only need a small subset of API endpoints to validate the most valuable UI flows.
- Booting the entire backend stack for every local Selenium run adds avoidable instability and setup cost.
- This host does not expose `node`/`pnpm` in `PATH`, so serving the compiled `dist/` bundles is the most reliable local execution path.

## Scope chosen

- Admin:
  - unauthenticated redirect
  - login
  - company list load
  - company creation
  - company detail navigation
- Client:
  - unauthenticated redirect
  - login
  - e-CF emission UI submit path
  - profile navigation
  - logout

## Tradeoff accepted

- These tests validate portal behavior and API contract assumptions for the mocked subset, not the full backend integration path.
- Because the suite serves `dist/`, frontend code changes require rebuilding the bundles before Selenium reflects them.
- Full-stack validation should remain a separate layer once a stable local DB-backed portal seed is available.
