**A. Arquitectura propuesta**

El modulo se implementa en [`app/dgii_portal_automation`](C:/Users/yoeli/Documents/dgii_encf/app/dgii_portal_automation) y separa autenticacion, navegacion, extraccion, descargas, reportes y seguridad. El `runtime` mantiene la sesion Playwright, la traza de auditoria y los artefactos descargados. Las tareas de negocio viven en `tasks.py` y solo coordinan componentes reutilizables; no contienen credenciales ni reglas de bajo nivel.

Relaciones principales:
- `config` centraliza variables de entorno, timeouts, rutas y modo de ejecucion.
- `runtime` crea `browser/context/page` y concentra auditoria.
- `auth` gestiona login, validacion, refresco y cierre de sesion.
- `navigation` resuelve menus y espera de carga.
- `extract` obtiene tablas, campos, mensajes y links de descarga.
- `downloads` controla descargas, hash, validacion y renombre contextual.
- `reporting` exporta a JSON, CSV y Excel y genera traza de auditoria.
- `safety` detecta acciones sensibles, exige confirmacion y redacta secretos.
- `tasks` encapsula flujos de consulta en modo reutilizable.

**B. Estructura de carpetas del proyecto**

```text
app/
  dgii_portal_automation/
    __init__.py
    auth.py
    cli.py
    config.py
    downloads.py
    errors.py
    extract.py
    models.py
    navigation.py
    reporting.py
    runtime.py
    safety.py
    tasks.py
    ui.py
scripts/
  automation/
    run_dgii_portal_task.py
tests/
  test_dgii_portal_automation.py
docs/
  guide/
    22-dgii-portal-automation.md
```

**C. Codigo base completo en Python con Playwright**

La implementacion real esta en:
- [`auth.py`](C:/Users/yoeli/Documents/dgii_encf/app/dgii_portal_automation/auth.py)
- [`navigation.py`](C:/Users/yoeli/Documents/dgii_encf/app/dgii_portal_automation/navigation.py)
- [`extract.py`](C:/Users/yoeli/Documents/dgii_encf/app/dgii_portal_automation/extract.py)
- [`downloads.py`](C:/Users/yoeli/Documents/dgii_encf/app/dgii_portal_automation/downloads.py)
- [`reporting.py`](C:/Users/yoeli/Documents/dgii_encf/app/dgii_portal_automation/reporting.py)
- [`safety.py`](C:/Users/yoeli/Documents/dgii_encf/app/dgii_portal_automation/safety.py)
- [`tasks.py`](C:/Users/yoeli/Documents/dgii_encf/app/dgii_portal_automation/tasks.py)
- [`cli.py`](C:/Users/yoeli/Documents/dgii_encf/app/dgii_portal_automation/cli.py)

Puntos tecnicos relevantes:
- No se inyecta JavaScript ni se altera el DOM.
- No se evaden captcha, MFA ni validaciones humanas.
- Las credenciales se toman solo desde variables de entorno.
- Playwright y `openpyxl` se cargan de forma lazy para mantener el modulo testeable sin dependencias pesadas en tiempo de import.

**D. Ejemplos de tareas automatizadas**

Comandos de ejemplo:

```powershell
$env:DGII_PORTAL_USERNAME="usuario"
$env:DGII_PORTAL_PASSWORD="secreto"
.\.venv312\Scripts\python.exe scripts\automation\run_dgii_portal_task.py login-check
.\.venv312\Scripts\python.exe scripts\automation\run_dgii_portal_task.py consulta-rnc --value 22500706423
.\.venv312\Scripts\python.exe scripts\automation\run_dgii_portal_task.py consulta-declaraciones --desde 2026-01-01 --hasta 2026-03-31
.\.venv312\Scripts\python.exe scripts\automation\run_dgii_portal_task.py consulta-pagos --desde 2026-01-01 --hasta 2026-03-31
.\.venv312\Scripts\python.exe scripts\automation\run_dgii_portal_task.py descarga-reportes --label descargar
.\.venv312\Scripts\python.exe scripts\automation\run_dgii_portal_task.py busqueda-por-periodo --section consulta --section pagos --desde 2026-01-01 --hasta 2026-03-31
```

Las funciones de negocio expuestas incluyen:
- `task_consulta_rnc()`
- `task_consulta_comprobantes()`
- `task_consulta_declaraciones()`
- `task_consulta_pagos()`
- `task_descarga_reportes()`
- `task_busqueda_por_periodo()`
- `task_exportacion()`

**E. Validaciones de seguridad y confirmacion**

La capa de seguridad esta en [`safety.py`](C:/Users/yoeli/Documents/dgii_encf/app/dgii_portal_automation/safety.py). Detecta verbos y contextos sensibles como `declarar`, `enviar`, `rectificar`, `pagar`, `confirmar`, `firmar`, `presentar` y `someter`.

Comportamiento:
- `read_only`: bloquea la accion y lanza error.
- `assisted`: prepara el resumen y exige autorizacion explicita antes de continuar.
- `redact_secrets()`: oculta usuario, password, bearer tokens, cookies y query params sensibles.
- `safe_screenshot()`: genera evidencia sin exponer campos tipo password/token.

**F. Recomendaciones de despliegue seguro**

- Ejecutar con un usuario de sistema dedicado y sin privilegios administrativos.
- Cargar secretos solo desde variables de entorno o un secret manager.
- Mantener el directorio de descargas fuera de carpetas sincronizadas publicamente.
- Restringir el uso del modulo a dominios DGII con `DGII_PORTAL_ALLOWED_DOMAINS`.
- Rotar credenciales y revisar expiracion de contrasenas institucionales.
- Separar `modo solo lectura` y `modo asistido` por ambiente o pipeline.
- En servidores, usar aislamiento por contenedor o VM y logs centralizados sin secretos.

**G. Riesgos tecnicos y mitigaciones**

- Cambios de layout o labels en DGII.
  Mitigacion: selectores semanticos y multiples hints por campo/boton.
- Retos humanos como captcha o MFA.
  Mitigacion: deteccion explicita y detencion del flujo para intervencion humana.
- Descargas corruptas o incompletas.
  Mitigacion: validacion de existencia, tamano y hash SHA-256.
- Sesiones expiradas.
  Mitigacion: `validate_session()` y `refresh_session()` antes de tareas.
- Fugas de secretos en trazas o capturas.
  Mitigacion: redaccion centralizada y blur de campos sensibles.

Variables de entorno principales:

```env
DGII_PORTAL_BASE_URL=https://dgii.gov.do
DGII_PORTAL_LOGIN_URL=https://dgii.gov.do/OFV/home.aspx
DGII_PORTAL_USERNAME=
DGII_PORTAL_PASSWORD=
DGII_PORTAL_MODE=read_only
DGII_PORTAL_ALLOWED_DOMAINS=dgii.gov.do,www.dgii.gov.do,ecf.dgii.gov.do,fc.dgii.gov.do
DGII_PORTAL_HEADLESS=true
DGII_PORTAL_BROWSER=chromium
DGII_PORTAL_TIMEOUT_MS=30000
DGII_PORTAL_NAV_TIMEOUT_MS=45000
DGII_PORTAL_ACTION_TIMEOUT_MS=20000
DGII_PORTAL_DOWNLOAD_DIR=artifacts_live_dns/dgii_portal/downloads
DGII_PORTAL_EXPORT_DIR=artifacts_live_dns/dgii_portal/exports
DGII_PORTAL_AUDIT_DIR=artifacts_live_dns/dgii_portal/audit
DGII_PORTAL_SCREENSHOT_DIR=artifacts_live_dns/dgii_portal/screenshots
```
