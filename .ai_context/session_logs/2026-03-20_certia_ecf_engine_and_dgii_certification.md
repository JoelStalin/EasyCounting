# Sesión 2026-03-20 — Certia ECF Engine, DGII Certification & Odoo Localization

## Resumen General
Esta sesión abarca desde la adaptación del módulo Odoo 15 a partir de la inspección del servidor de producción (`jabiya`), pasando por la certificación real DGII vía OFV con automatización browser, hasta el re-diseño arquitectónico de Certia como motor centralizado de generación de comprobantes electrónicos.

---

## Acciones Completadas

### 1. Odoo 15 — Adaptación Módulo `getupsoft_do_localization`
- Se creó `hooks.py` en `integration/odoo/odoo15_getupsoft_do_localization/l10n_do_accounting/` con la función `auto_configure_l10n_do_base`.
- Se inyectó la llamada al hook desde `__init__.py` dentro del `_l10n_do_accounting_post_init`.
- Los hooks configuran automáticamente: Diarios LATAM, País República Dominicana (RD), Moneda DOP.
- Basado en el análisis del módulo `neo_do_localization` en producción (Jabiya SSH).

### 2. Entorno Lab Odoo 15 — `odoo15_testing_env`
- Nuevo ambiente Docker en `c:\Users\yoeli\Documents\dgii_encf\labs\odoo15_testing_env\`
- Puerto: `15070:8069`
- Red Docker nombrada: `odoo-test-net`
- DB: `certia_odoo15_lab` en Postgres 15 (volume nombrado `postgres-db-data`)
- Config: `config/odoo.conf` apuntando a addons getupsoft y enterprise
- Scripts de utilidad:
  - `setup_country_currency_15.py` → Exitoso (País: RD, Moneda: DOP configurados)
  - `check_mods.py` → Verificar estados de módulos instalados
  - `force_install.py` → Forzar instalación sin Alembic

### 3. Proceso Real de Certificación DGII (Portal OFV)
- Se accedió con éxito a `https://ecf.dgii.gov.do` usando RNC `22500706423`.
- Se actualizaron **las 3 URLs** del formulario "Paso 1: Registrado":
  - URL de recepción → `https://api.getupsoft.com.do/fe/recepcion/api/ecf`
  - URL de aprobación comercial → `https://api.getupsoft.com.do/fe/aprobacioncomercial/api/ecf`
  - URL de autenticación → `https://api.getupsoft.com.do/fe/autenticacion/api/[semilla|validacioncertificado]`
- Se hizo clic en "GENERAR ARCHIVO" → La DGII confirmó el archivo XML generado.
- **Paso Pendiente (Manual):** Firmar el XML con el Certificado P12 y enviarlo vía "ENVIAR ARCHIVO".

### 4. Cloudflare Tunnel — Verificación de Endpoints Públicos
- Confirmado que el proceso `cloudflared` está activo en Windows (PID ~20488).
- `https://api.getupsoft.com.do/livez` → HTTP 200 OK `{"status":"alive"}`
- El backend está VIVO y es accesible desde la internet pública.

### 5. Set de Pruebas DGII (Pre-Certificación)
- Script creado: `labs/odoo15_testing_env/dgii_test_set_runner.py`
- Emite las siguientes series en Odoo 19 (`chefalitas19lab`):
  - e-CF 31 (Crédito Fiscal B2B) → `emit_ecf('Crédito Fiscal Electrónica', ...)`
  - e-CF 32 (Consumo B2C) → `emit_ecf('Consumo Electrónica', ...)`
  - e-CF 33 (Nota de Crédito) → via `account.move.reversal`
- Ejecutado contra Odoo 19 con resultados positivos (no hubo errores de DB).

### 6. Re-Arquitectura: Certia como Motor Maestro de E-CF

#### Nuevo Modelo de Datos: `app/models/sequence.py`
```python
class Sequence(Base):
    __tablename__ = "sequences"
    tenant_id: Mapped[int]    # FK a tenants.id
    doc_type: Mapped[str]     # '31', '32', '33', etc.
    prefix: Mapped[str]       # 'E31', 'E32', etc.
    next_number: Mapped[int]  # Incremental único por tenant+doc_type
    # UniqueConstraint(tenant_id, doc_type)
```

#### Nuevo Endpoint: `POST /api/v1/ecf/generate`
- Archivo: `app/routers/ecf.py`
- Lógica:
  1. Obtiene el tenant por `certia_tenant_id`
  2. Verifica que tenga un plan asignado
  3. Cuenta el uso mensual vs `plan.max_facturas_mes`
  4. Si excede → HTTP 402 con detalle del límite
  5. Asigna el siguiente NCF de la Sequence table (ej. `E3100000001`)
  6. Registra un `UsageRecord` con el TrackId
  7. Retorna JSON con `ncf`, `track_id`, `quota`, `odoo_payload`

#### Registro en `app/main.py`
```python
from app.routers.ecf import router as ecf_router
app.include_router(ecf_router, prefix="/api/v1/ecf", tags=["ecf-master-engine"])
```

#### Migración de DB
- `alembic upgrade head` ejecutado en `dgii_encf-web-1` → Exitoso (exit 0)
- La nueva tabla `sequences` se genera vía `alembic revision --autogenerate` → Pendiente confirmar

---

## Estado Actual de los Contenedores Docker
| Contenedor | Imagen | Estado |
|---|---|---|
| `dgii_encf-web-1` | FastAPI Backend | RUNNING |
| `dgii_encf-db-1` | Postgres 16 | RUNNING |
| `dgii_encf-nginx-1` | Nginx 1.27 | RUNNING |
| `odoo19_chefalitas-odoo-1` | Odoo 19 | RUNNING |
| `odoo15_test_web` | Odoo 15.0 | RUNNING |
| `getupsoft_odoo15-odoo-1` | Getupsoft Odoo 15 | RUNNING |

---

## Archivos Clave Creados/Modificados
| Archivo | Acción |
|---|---|
| `app/models/sequence.py` | NUEVO — Modelo de Secuencias NCF |
| `app/routers/ecf.py` | NUEVO — Motor Master E-CF con cuotas |
| `app/models/__init__.py` | MODIFICADO — Importa `sequence` |
| `app/main.py` | MODIFICADO — Monta `ecf_router` |
| `labs/odoo15_testing_env/dgii_test_set_runner.py` | NUEVO — Set de Pruebas DGII |
| `labs/odoo15_testing_env/docker-compose.yml` | NUEVO — Lab Odoo 15 |
| `labs/odoo15_testing_env/config/odoo.conf` | NUEVO — Config Lab |
| `integration/odoo/.../l10n_do_accounting/hooks.py` | NUEVO — Auto-configuración Odoo 15 |

---

## Pending / Próximos Pasos
1. **[USUARIO]** Firmar el XML generado con el certificado P12 y enviarlo a la DGII → Paso 1 de Certificación.
2. Ejecutar `alembic revision --autogenerate` en `dgii_encf-web-1` para generar el script de migración de la tabla `sequences`.
3. Implementar el **Consumidor Odoo** → En Odoo 19/15 un CRON o script que haga `GET /api/v1/ecf/sync?company_id=X` y que inyecte los recibos en `account.move`.
4. Crear scrip Odoo que haga POST a `/api/v1/ecf/generate` desde Odoo al confirmar una factura.
5. Crear Empresas Demo en el Portal Admin de Certia con límites de plan asignados para testing de cuotas.
