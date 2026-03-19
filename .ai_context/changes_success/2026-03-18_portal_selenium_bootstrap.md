# Successful Change - 2026-03-18

- Added `.ai_context` structure and baseline project context for `dgii_encf`.
- Replaced placeholder Selenium tests with functional portal flows.
- Added a deterministic local mock API for auth and admin tenant CRUD.
- Switched the Selenium harness to serve compiled portal bundles from `frontend/apps/*/dist`, which avoids dependency on missing local Node tooling.
- Validation completed with `2 passed in 24.89s`.
