# Module Inventory - 2026-03-18

Coverage legend:

- `executed`: validated through Selenium in this session
- `indirect`: exercised by navigation/auth shell but not asserted deeply
- `static`: inspected structurally, not executed by Selenium this round

## Frontend apps

- `admin-portal` | path: `frontend/apps/admin-portal` | crit: high | auth: `PLATFORM` | tests: yes | coverage: executed
- `client-portal` | path: `frontend/apps/client-portal` | crit: high | auth: `TENANT` | tests: yes | coverage: executed

## Admin portal slices

- `pages/Login.tsx` | crit: high | purpose: first-factor auth UI | coverage: executed
- `pages/Companies.tsx` | crit: high | purpose: tenant listing and creation | coverage: executed
- `pages/CompanyDetail.tsx` | crit: high | purpose: tenant detail and tab shell | coverage: executed
- `components/AppLayout.tsx` | crit: high | purpose: auth shell, nav, logout | coverage: executed
- `api/tenants.ts` | crit: high | purpose: list/create/get tenant contract | coverage: executed
- `pages/Dashboard.tsx` | crit: medium | purpose: platform KPI landing | coverage: indirect
- `pages/Plans.tsx` | crit: medium | purpose: plan management | coverage: static
- `pages/AuditLogs.tsx` | crit: medium | purpose: audit visibility | coverage: static
- `pages/Users.tsx` | crit: medium | purpose: platform RBAC users | coverage: static

## Client portal slices

- `pages/Login.tsx` | crit: high | purpose: tenant auth UI | coverage: executed
- `pages/EmitECF.tsx` | crit: high | purpose: tenant e-CF submit UX | coverage: executed
- `pages/Profile.tsx` | crit: medium | purpose: session and permission visibility | coverage: executed
- `components/AppLayout.tsx` | crit: high | purpose: nav and logout | coverage: executed
- `api/auth.ts` | crit: high | purpose: portal auth contract | coverage: executed
- `pages/Invoices.tsx` | crit: high | purpose: document browsing | coverage: static
- `pages/Plans.tsx` | crit: medium | purpose: plan change UX | coverage: static
- `pages/Approvals.tsx` | crit: medium | purpose: approval workflow | coverage: static
- `pages/Certificates.tsx` | crit: medium | purpose: certificate management | coverage: static

## E2E harness

- `e2e/conftest.py` | crit: high | purpose: start mock API, static portal servers, Selenium driver, artifacts | coverage: executed
- `e2e/mock_api.py` | crit: high | purpose: deterministic API subset for portal flows | coverage: executed
- `e2e/tests/test_admin_smoke.py` | crit: high | purpose: admin functional flow | coverage: executed
- `e2e/tests/test_client_smoke.py` | crit: high | purpose: client functional flow | coverage: executed
