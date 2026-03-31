# Change Log

## 2026-03-25

- Mounted real DGII routers before legacy compatibility router.
- Added durable fiscal operation domain and persistence for events, attempts, evidence, and coverage.
- Added accounting hardening migration `20260325_0001_fiscal_ops_and_accounting_hardening.py`.
- Added controlled browser automation module with feature flags.
- Produced reproducible local evidence in `tests/artifacts/2026-03-25_23-50-25_controlled_local_matrix/`.

## 2026-03-28 (sesión 2 — corrección JSONB + validación completa)

### Fix JSONB → PortableJSONB (compatibilidad SQLite en tests)
- Creado `app/shared/types.py`:
  - `PortableJSONB(TypeDecorator)`: usa `JSONB` en PostgreSQL, `JSON` en SQLite y otros dialectos.
  - Permite que `Base.metadata.create_all()` funcione en tests sin PostgreSQL.
- Actualizado `app/models/odoo_mirror.py`:
  - Reemplazado `from sqlalchemy.dialects.postgresql import JSONB` por `from app.shared.types import PortableJSONB`.
  - Columnas `raw_json` (OdooPartnerMirror, OdooProductMirror, OdooInvoiceMirror) y `lines_json` (OdooInvoiceMirror) ahora usan `PortableJSONB`.
- Resultado: `pytest tests/test_fiscal_operations.py tests/test_clients_contract.py -q` → **5 passed** (antes: 4 failed).

### Validación completa de suite de tests
- `pytest tests/test_fiscal_operations.py tests/test_clients_contract.py -q` → **5 passed** ✅
- `pytest automation/browser/tests/test_browser_feature_flags.py -q` → **5 passed** ✅
- `pnpm --filter @getupsoft/admin-portal exec tsc --noEmit` → **exit 0** ✅
- `python -m compileall app automation tests -q` → **exit 0** ✅

---

## 2026-03-28 (sesión 1 — implementación tareas pendientes)

- Implementadas todas las tareas pendientes del contexto IA (`19-next-steps.md`):

### Migración staging + consolidación de duplicados
- Creada migración `alembic/versions/20260328_0001_staging_dedup_and_constraints.py`:
  - Índices de rendimiento adicionales en `fiscal_operations` (env+state, dgii_status, odoo_sync_state, completed_at).
  - Índices en `invoices` (odoo_sync_state, tenant+fecha_emision).
  - Índice en `fiscal_operation_events` (operation_fk + occurred_at DESC) para SSE stream.
  - Índices en `dgii_attempts`, `odoo_sync_attempts`, `comprobante_coverage_results`.
- Creado `scripts/staging_dedup_check.py`:
  - Audita duplicados de `operation_key` en `fiscal_operations`.
  - Audita duplicados de `tenant_id+encf` en `invoices`.
  - Modo `--dry-run` (default) y `--fix` con confirmación.
  - Reasigna eventos, intentos, evidencias y líneas antes de eliminar duplicados.
  - Imprime estadísticas de tablas y desglose de estados.

### Admin portal — SSE real-time stream
- Actualizado `frontend/apps/admin-portal/src/api/operations.ts`:
  - Añadido hook `useOperationStream(operationId)` con `EventSource` nativo.
  - Deduplicación de eventos por `id`.
  - Estado de conexión: `connecting | connected | error | closed`.
  - Fallback automático a polling si SSE falla o no está soportado.
- Reescrito `frontend/apps/admin-portal/src/components/OperationMonitor.tsx`:
  - Conectado al stream SSE real del endpoint `GET /api/v1/operations/{id}/stream`.
  - Badge de estado de conexión (SSE en vivo / Conectando / Polling / Inactivo).
  - Merge de eventos SSE + polling con deduplicación por `id`.
  - Timeline de eventos con colores por estado DGII.
  - Panel de evidencia y métricas de operación.
  - Indicador de eventos en vivo (`+N en vivo`).

### Fix asyncio.run() en thread (jobs.py)
- Corregido `app/dgii/jobs.py`:
  - `_persist_status_and_sync` usaba `asyncio.run()` dentro de un thread que puede tener un event loop activo.
  - Reemplazado por `asyncio.new_event_loop()` + `loop.run_until_complete()` + `loop.close()` para aislamiento seguro.

### Browser automation — hardening modo evidence-only
- Refactorizado `automation/browser/config.py`:
  - Constantes canónicas: `EVIDENCE_ONLY`, `ASSISTIVE`, `FULL`.
  - Normalización y validación de modo al cargar settings (default: `evidence-only`).
  - Nuevos guards: `ensure_evidence_only_mode()`, `ensure_assistive_or_evidence()`, `assert_no_write_actions(action)`.
  - Propiedades: `is_evidence_only`, `is_assistive`, `writes_permitted`.
  - `__str__` para logging legible.

## 2026-03-29

### Sesión 2 — Corrección de tests fallidos, errores de colección y bug de runtime

#### Correcciones de código

- **`app/shared/storage.py`** — Añadido `_json_default` encoder en `store_json()` para serializar `Decimal` (→ `float`) y `datetime` (→ ISO 8601). Resuelve `TypeError: Object of type Decimal is not JSON serializable` en `test_tenant_api_token_can_read_and_register_invoices`.
- **`app/dgii/jobs.py`** — Añadido flag `item_retrieved` en `_consume()` para proteger `task_done()` de ser llamado cuando `asyncio.Queue.get()` lanza `CancelledError` antes de entregar un ítem. Elimina `ValueError: task_done() called too many times` en shutdown.
- **`app/services/ai/providers/openai.py`** — Eliminado `raise ValueError` cuando `base_url` es `None`; se usa `"https://api.openai.com/v1"` como valor por defecto. Permite que `OpenAIProvider` funcione sin configuración explícita de `base_url`.
- **`app/services/ai/orchestrator.py`** — Corregido campo `engine` en el dict de retorno: era `response.model`, ahora es `response.provider`. Añadido campo `model` separado con `response.model`. Alinea la respuesta con las aserciones del test y con la semántica esperada.

#### Correcciones de tests

- **`tests/test_admin_ai_providers.py`** — Reemplazado mock síncrono `fake_post` (que parchaba `app.application.tenant_chat.httpx.post`) por `_MockAsyncClient` (async context manager) que parchea `app.services.ai.providers.openai.httpx.AsyncClient`. Refleja el uso real de `async with httpx.AsyncClient(...)` en `OpenAIProvider.chat()`.
- **`tests/test_e2e_local.py`** — Añadido `import socket`, helper `_db_reachable()` y decorador `@pytest.mark.skipif(not _db_reachable(), ...)` en `test_e2e_seed_token_send_ecf_status_and_ri`. El test se omite automáticamente fuera de Docker network donde `db:5432` no es alcanzable.
- **`tests/test_dgii_rnc_web_parser.py`** — Corregido `MODULE_PATH`: `"getupsoft_do_localization"` → `"odoo19_getupsoft_do_localization"`. Resuelve `CollectionError` por ruta de módulo incorrecta.
- **`tests/test_odoo_payloads.py`** — Reemplazado `import requests` (falla en colección si no instalado) por `requests = pytest.importorskip("requests", ...)`. El módulo se omite limpiamente cuando `requests` no está disponible.

#### Archivos de infraestructura creados (sesión 2)

- **`app/shared/types.py`** — `PortableJSONB` TypeDecorator para SQLAlchemy (serialización JSONB portable entre PostgreSQL y SQLite).
- **`app/models/odoo_mirror.py`** — Migrado de `JSONB` a `PortableJSONB`.
- **`alembic/versions/20260328_0001_staging_dedup_and_constraints.py`** — Migración de deduplicación y restricciones únicas para staging.
- **`scripts/staging_dedup_check.py`** — Script de verificación de duplicados antes de aplicar restricciones únicas.
- **`app/application/lifecycle.py`** — Orquestación de startup/shutdown de la aplicación.
- **`app/application/router_registration.py`** — Helper `include_router_entries()` para registro de routers.
- **`app/tests/unit/test_router_registration.py`** — Tests unitarios de registro de routers.
- **`app/tests/unit/test_settings_runtime_flags.py`** — Tests unitarios de flags de runtime en settings.
- **`app/infra/settings.py`** — Añadido campo computado `is_production`.
- **`automation/browser/config.py`** — Reescrito con constantes canónicas.
- **`frontend/apps/admin-portal/src/api/operations.ts`** — Hook SSE actualizado.
- **`frontend/apps/admin-portal/src/components/OperationMonitor.tsx`** — Componente reescrito.
- **`TODO.md`** — Creado y actualizado con tareas 1-19.

#### Resultado de tests al cierre de sesión 2

- `tests/test_admin_ai_providers.py` — **4 passed** ✅
- `tests/test_e2e_local.py` — **1 skipped** (DB no alcanzable fuera de Docker) ✅
- `tests/test_dgii_rnc_web_parser.py` — **4 passed** ✅
- `tests/test_odoo_payloads.py` — **1 skipped** (`requests` no instalado) ✅
- `app/tests/unit/` — **22 passed** ✅
- Tests fallidos previos resueltos: **3 FAILED → 0 FAILED**
- Errores de colección resueltos: **2 CollectionError → 0**

---

## 2026-03-30

- Started Docker Desktop and all services using `docker-compose up -d`.
- Started Cloudflare tunnel using `scripts/automation/start_cloudflared_quick_tunnel.ps1`.
- Ran E2E tests for front-ends using `scripts/automation/run_selenium_live.ps1` (live Selenium mode).
- Fixed VAT validation error in `scripts/automation/odoo19_chefalitas/provision_lab_odoo.py` by changing VAT to `13199999999`.
- Re-provisioned Odoo 19 lab environment.
- Installed missing `getupsoft_l10n_do_e_accounting` module in Odoo 19 lab environment.
- Ran Odoo comprobante matrix tests using `scripts/automation/odoo19_run_comprobante_matrix.py` successfully (14 posted, 0 failed).

---

## 2026-03-26

- Implemented tenant certificate service and endpoints:
  - `GET /api/v1/cliente/certificates`
  - `POST /api/v1/cliente/certificates`
  - `POST /api/v1/cliente/certificates/sign-xml`
  - `POST /api/v1/internal/certificates/sign-xml`
  - `POST /api/v1/internal/certificates/register`
- Hardened internal origin validation for loopback/private bridge with `X-Internal-Secret`.
- Made certificate registration idempotent for existing tenant certificate.
- Updated DGII pipeline to prioritize tenant active certificate and safe environment fallback.
- Aligned RFCE, ANECF, ACECF, and ARECF routes with tenant/RNC certificate resolution.
- Re-ran backend tests:
  - `pytest tests/test_tenant_certificates.py tests/test_fiscal_operations.py -q`
  - Result: `8 passed`.
- Re-ran controlled local matrix with amount `0.001`:
  - `tests/artifacts/2026-03-26_02-13-10_controlled_local_matrix/`.
- Re-ran real DGII Selenium postulation and documented gates:
  - `tests/artifacts/2026-03-26_02-13-52_dgii_real_postulacion_ofv/`
  - Gate: `409 No existe un certificado utilizable para firmar`.
- Confirmed real DGII validation that `VersionSoftware` must be numeric (`double`) and normalized script behavior to `1.0`.
- Added `scripts/automation/sign_postulacion_xml.py` (`internal sign -> register -> sign -> local fallback`).
- Validated real run with automatic sign+upload:
  - `tests/artifacts/2026-03-26_02-33-33_dgii_real_postulacion_ofv/`
  - DGII response: `Error XML. Firma Invalida.`
- Expanded official investigation for valid postulation signature:
  - CA5241, CA5268, CA5270, `Firmado de e-CF`, Resolucion 035-2020.
- Added Windows certificate store signing tool:
  - `scripts/automation/sign_with_windows_certstore.ps1`
- Added Windows cert inventory tool:
  - `scripts/automation/list_windows_signing_certificates.ps1`
- Updated `scripts/automation/run_real_dgii_postulacion_ofv.py` to prioritize:
  1. Windows store signature
  2. DGII App Firma Digital
  3. Internal API and register fallback
- Rewrote `scripts/automation/REAL_CERTIFICATION_RUNBOOK.md` with updated signature requirements and tools.
- Executed real Selenium postulation using Windows store signer:
  - `tests/artifacts/2026-03-26_03-06-33_dgii_real_postulacion_ofv/`
  - Signature mode: `signed_with_windows_store`
  - Upload attempted: `true`
  - DGII response: `La firma utilizada en el XML del formulario de postulacion no corresponde con el representante registrado...`
  - Conclusion: automation path works; real representative certificate is still missing.
