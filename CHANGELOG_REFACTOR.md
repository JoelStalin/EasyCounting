# Changelog Refactor

## 2026-03-30 — Fase incremental 1 (bajo riesgo)

### Qué se cambió
1. **Extracción de helper de registro de routers**
   - Nuevo módulo: `app/application/router_registration.py`.
   - Se centraliza la inclusión repetitiva de routers para prefijos compartidos.
2. **Refactor no funcional en `app/main.py`**
   - Se reemplazó duplicación de `app.include_router(...)` para bloques versionados/legacy por listas declarativas + helper.
   - Se mantiene el mismo comportamiento, rutas y prefijos.
3. **Artefactos de recuperación y baseline**
   - `RECOVERY_NOTES.md`.
   - `tests/functional/SMOKE_CHECKLIST_PRE_REFACTOR.md`.

### Por qué se cambió
- Reducir duplicación y riesgo de drift entre rutas `/api/v1` y `/api`.
- Mejorar legibilidad de composición del API sin alterar contratos existentes.
- Dejar capacidad de rollback clara antes de fases de refactor mayores.

### Riesgos
- Riesgo bajo: un error en el helper de inclusión podría omitir o mal etiquetar un router.
- Mitigación: helper minimalista y sin transformación de prefijos ni paths.

### Cómo restaurar si algo sale mal
- Revertir commit del bloque de refactor:
  - `git revert <commit_sha>`
- O restaurar snapshot completo:
  - `git checkout backup/pre-refactor-20260330-0315`
  - `git checkout pre-refactor-stable-20260330-0315`
  - `rsync -a /backup/pre-refactor-20260330-0315/ /workspace/EasyCounting/`

## 2026-03-30 — Fase incremental 2 (bajo riesgo)

### Qué se cambió
1. **Extracción de orquestación de lifecycle**
   - Nuevo módulo: `app/application/lifecycle.py`.
   - Se movió desde `app/main.py` la lógica de startup/shutdown de dependencias runtime y jobs.
2. **Simplificación de `lifespan` en `app/main.py`**
   - `lifespan` ahora delega en funciones de application layer.
3. **Pruebas unitarias nuevas**
   - `app/tests/unit/test_router_registration.py` para validar helper de registro de routers.

### Por qué se cambió
- Reducir responsabilidades directas en `app/main.py`.
- Facilitar evolución futura de lifecycle sin tocar bootstrap HTTP.
- Mejorar validación automática del refactor previo de router registration.

### Riesgos
- Riesgo bajo: cambio estructural sin modificar contratos de endpoint.
- Mitigación: funciones extraídas mantienen la misma secuencia de arranque/parada.

### Cómo restaurar si algo sale mal
- Revertir commit de esta fase.
- O restaurar rama/tag/copia física de pre-refactor indicados en `RECOVERY_NOTES.md`.

## 2026-03-30 — Fase incremental 3 (bajo riesgo)

### Qué se cambió
1. **Lifecycle con imports diferidos (lazy imports)**
   - `app/application/lifecycle.py` ahora importa jobs/rate limiter dentro de cada función.
   - Se reduce el acoplamiento en tiempo de import del módulo.
2. **Flag semántica de entorno**
   - `app/infra/settings.py` incorpora `is_production` como computed field reutilizable.
   - `app/main.py` y `app/application/lifecycle.py` migran de checks repetidos a `settings.is_production`.
3. **Pruebas unitarias adicionales de configuración**
   - `app/tests/unit/test_settings_runtime_flags.py` valida `is_production`.

### Por qué se cambió
- Evitar side effects y dependencias pesadas en import-time.
- Centralizar la regla de entorno productivo en un único punto.
- Mejorar consistencia y mantenibilidad en decisiones de runtime.

### Riesgos
- Bajo: no cambia contratos HTTP ni payloads.
- Mitigación: cambios acotados a composición/runtime flags.

### Cómo restaurar si algo sale mal
- Revertir commit de esta fase.
- O restaurar backup/tag/copia física pre-refactor.
