# Next Steps

## Completados (2026-03-28)

3. ✅ **Migración staging + consolidación de duplicados**
   - Migración `20260328_0001_staging_dedup_and_constraints.py` creada con índices de rendimiento.
   - Script `scripts/staging_dedup_check.py` para auditar y consolidar duplicados antes de migrar.
   - Procedimiento: `python scripts/staging_dedup_check.py --dry-run` → `--fix --yes` → `alembic upgrade head`.

4. ✅ **Admin portal conectado al stream SSE real**
   - Hook `useOperationStream` con `EventSource` nativo + fallback a polling.
   - `OperationMonitor` muestra badge de estado SSE, merge de eventos en tiempo real y colores por estado.
   - Endpoint backend: `GET /api/v1/operations/{operation_id}/stream`.

5. ✅ **Browser automation en modo `evidence-only` (hardening)**
   - `automation/browser/config.py` refactorizado con constantes canónicas y guards explícitos.
   - `ensure_evidence_only_mode()`, `assert_no_write_actions()`, `ensure_assistive_or_evidence()`.
   - Normalización automática de modo al cargar settings (default: `evidence-only`).

   **Fix adicional:**
   - `app/dgii/jobs.py`: `asyncio.run()` dentro de thread reemplazado por `asyncio.new_event_loop()` + `loop.run_until_complete()` + `loop.close()`.

---

## Pendientes — bloqueados por gate externo

1. **Cargar secretos reales DGII en `TEST` y ejecutar la matriz oficial**
   - Requiere: certificado real `cert.p12` para RNC 22500706423 (representante legal registrado ante DGII).
   - Requiere: credenciales de acceso al portal DGII TEST/CERT.
   - Acción: cuando se disponga del certificado, ejecutar `scripts/run_local_controlled_matrix.py` apuntando a `TEST`.
   - Referencia: `DEC-004-real-signature-paths.md`, `scripts/automation/REAL_CERTIFICATION_RUNBOOK.md`.

2. **Configurar Odoo 19 JSON-2 real y validar `SYNCED_TO_ODOO`**
   - Requiere: endpoint real Odoo 19, base de datos y API key.
   - Variables: `ODOO_JSON2_BASE_URL`, `ODOO_JSON2_DATABASE`, `ODOO_JSON2_API_KEY`.
   - Acción: configurar `TenantSettings.odoo_sync_enabled=True` y ejecutar un e-CF de prueba.
   - Referencia: `08-odoo-easycounting-compatibility.md`, `app/application/accounting_sync.py`.

---

## Completados (2026-03-28 sesión 2)

6. ✅ **Fix JSONB → PortableJSONB (compatibilidad SQLite en tests)**
   - Creado `app/shared/types.py` con `PortableJSONB(TypeDecorator)`.
   - Actualizado `app/models/odoo_mirror.py` para usar `PortableJSONB` en todas las columnas JSON.
   - Resultado: 4 tests que fallaban ahora pasan.

7. ✅ **Validación completa de suite de tests**
   - `pytest tests/test_fiscal_operations.py tests/test_clients_contract.py -q` → **5 passed** ✅
   - `pytest automation/browser/tests/test_browser_feature_flags.py -q` → **5 passed** ✅
   - `pnpm --filter @getupsoft/admin-portal exec tsc --noEmit` → **exit 0** ✅
   - `python -m compileall app automation tests -q` → **exit 0** ✅

---

## Próximos pasos sugeridos

- Aplicar migración en staging: `python scripts/staging_dedup_check.py --dry-run` → `alembic upgrade head`.
- Documentar política de secuencias por tenant y compañía Odoo (ver `18-open-questions.md`).
- Validar mínimos monetarios en sandbox oficial DGII cuando se disponga de credenciales.
- Definir política de despliegue del módulo browser automation (contenedor dedicado vs runner separado).
