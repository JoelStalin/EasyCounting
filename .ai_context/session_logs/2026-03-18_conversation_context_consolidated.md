# Consolidated Conversation Context - 2026-03-18

## Scope

This note consolidates the important technical context produced across the current working conversation for `dgii_encf`.

Sensitive values shared in chat are intentionally **not** copied here. Any DGII passwords, AWS secrets, tokens, session keys, or certificate passwords must live in approved secret storage only and should be rotated if they were exposed in plain text.

## Project identity

- Workspace root: `C:\Users\yoeli\Documents\dgii_encf`
- Primary backend: FastAPI app in `app/`
- Frontend: React/Vite workspaces in `frontend/apps/admin-portal` and `frontend/apps/client-portal`
- Optional ERP integration assets: `integration/odoo/getupsoft_do_localization`
- Testing harness: `tests/` and `e2e/`

## Most important outcomes from this conversation

### 1. AI context and project traceability were established

- A structured `.ai_context/` directory was created and populated.
- Runbooks, snapshots, test evidence, risk notes, and change logs were added.
- The repo now has persistent local context instead of relying on chat memory alone.

### 2. Functional browser testing was implemented and executed

- Selenium E2E coverage was added under `e2e/`.
- A visual live run was executed in headed mode with screenshots and HTML report output.
- Current known evidence:
  - `e2e/artifacts/live_20260318_154623/report.html`
  - `.ai_context/test_evidence/2026-03-18_selenium_live_demo.md`

### 3. Odoo localization was imported, renamed, and versioned for Odoo 19

- Remote `neo_do_localization` was copied from `jabiya`.
- A full local variant was created as `getupsoft_do_localization`.
- Branding and authorship were moved to GetUpSoft.
- Module manifests were updated to the Odoo 19 line.
- Legacy POS pieces that were not yet Odoo 19 compatible were left non-installable instead of pretending runtime compatibility.

### 4. Odoo partner enrichment was reworked for this project

- Partner lookup/autocomplete now supports official DGII RNC/Cedula consultation through the public DGII page.
- Local fallback was added through internal backend endpoints and then local Odoo records.
- This reduced dependence on third-party non-official services while preserving a deterministic internal fallback.

### 5. A tenant-scoped chatbot was added

- Backend service: `app/application/tenant_chat.py`
- Route: `POST /api/v1/cliente/chat/ask`
- Frontend source page: `frontend/apps/client-portal/src/pages/Assistant.tsx`
- Security model:
  - answers only from the authenticated tenant dataset
  - platform roles are rejected
  - explicit references outside the tenant scope do not leak cross-tenant data
- Engines supported:
  - `local`
  - `openai_compatible`

### 6. Local WSL execution path was prepared

- A local WSL-oriented compose file and nginx config were created.
- Validation was documented.
- A known issue was logged for unstable Docker/WSL runtime behavior on this host.

### 7. External-service minimization was enforced where possible

- Odoo RNC support now prefers:
  1. official DGII public source
  2. internal backend service
  3. local Odoo data
- Third-party SOAP-style dependencies previously present in the imported localization were removed or bypassed.

## Security-sensitive decisions taken

- Do not use AWS root credentials for automation.
- Prefer temporary AWS credentials and least privilege.
- Do not store secrets in repo docs.
- DGII OFV username/password alone is not enough for real emission certification; the digital certificate (`.p12`) and password are required for semilla -> signed semilla -> token flow.
- Tenant chat must never answer with other tenants' data.

## Current architecture snapshot from code

### Backend

- `app/main.py` mounts:
  - portal auth routes under `/auth` and `/api/v1/auth`
  - admin routes under `/api/v1/admin`
  - tenant routes under `/api/v1/cliente`
  - local Odoo helper routes under `/api/v1/odoo`
  - legacy compatibility routes under `/api`
- Infra concerns already wired:
  - Prometheus `/metrics`
  - Sentry optional
  - Redis-backed rate limiting in production
  - readiness probes for DB and Redis

### Frontend

- Admin portal scope: `PLATFORM`
- Client portal scope: `TENANT`
- Both SPAs use route guards plus bearer-token API clients.
- Client portal includes a tenant assistant route.

### Odoo integration

- Current repo contains Odoo addon assets, not yet a production JSON-RPC bridge service.
- The future `odoo_integration` service is still a planned component, not a deployed runtime in this repo.

## Current blockers and open gaps

### Real DGII certification is still blocked

- Missing real tenant certificate path (`.p12`)
- Missing certificate password
- Missing runtime evidence against DGII `CERT` with a valid authorized emitter context

### Frontend build gap

- Node/pnpm were not available in `PATH` on this host during the earlier work.
- Frontend source changes were made, but not rebuilt into fresh `dist` bundles in this session.

### Odoo runtime gap

- Odoo 19 compatibility was validated statically, not by booting a real Odoo 19 instance here.
- The addon tree exists, but the API bridge service and end-to-end accounting sync are still pending.

### Infrastructure gap

- Local Docker/WSL was not stable enough to treat as a production-like certification environment.
- AWS automation scripts exist, but they must run with temporary IAM credentials, not root credentials.

## Evidence produced so far

- Selenium live evidence:
  - `.ai_context/test_evidence/2026-03-18_selenium_live_demo.md`
  - `e2e/artifacts/live_20260318_154623/report.html`
- WSL local service evidence:
  - `.ai_context/test_evidence/2026-03-18_wsl_local_service_validation.md`
- Odoo import/refactor evidence:
  - `.ai_context/changes_success/2026-03-18_jabiya_neo_do_localization_snapshot.md`
  - `.ai_context/changes_success/2026-03-18_getupsoft_localization_refactor.md`
  - `.ai_context/changes_success/2026-03-18_odoo19_versioning.md`
- Odoo RNC autocomplete evidence:
  - `.ai_context/changes_success/2026-03-18_dgii_web_rnc_autocomplete.md`
- Chatbot evidence:
  - `.ai_context/changes_success/2026-03-18_tenant_chatbot_llm.md`

## Strategic priorities after this consolidation

1. Close the DGII certification prerequisites using a valid emitter certificate and controlled test payloads.
2. Convert the Odoo asset tree into a real bridge service with tenant-safe synchronization.
3. Rebuild frontend bundles from source with a stable Node toolchain.
4. Formalize CI quality gates for secrets, security scans, tests, and artifact generation.
5. Move remaining operational assumptions from chat into repo-owned runbooks and ADR-style notes.
