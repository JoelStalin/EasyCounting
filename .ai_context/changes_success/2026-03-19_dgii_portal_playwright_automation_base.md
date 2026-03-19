Fecha: 2026-03-19

Resumen:
- Se agregó un paquete modular `app/dgii_portal_automation` como base profesional para automatizar consultas seguras en el portal DGII con Playwright.
- La implementación quedó separada por capas: `auth`, `navigation`, `extract`, `tasks`, `downloads`, `reporting`, `safety`, `config`, `runtime` y `cli`.
- No se codificaron credenciales ni se reutilizaron secretos de la conversación dentro del código o de los logs.

Archivos clave:
- `app/dgii_portal_automation/*.py`
- `scripts/automation/run_dgii_portal_task.py`
- `docs/guide/22-dgii-portal-automation.md`
- `tests/test_dgii_portal_automation.py`
- `.env.example`
- `requirements-dev.txt`
- `pyproject.toml`

Decisiones:
- Carga lazy de `playwright` y `openpyxl` para que el paquete pueda importarse y probarse sin instalar esas dependencias inmediatamente en esta shell.
- Acciones sensibles bloqueadas en `read_only` y confirmadas en `assisted`.
- Evidencia segura con redaccion de secretos y blur de inputs sensibles en capturas.

Pendientes operativos:
- Instalar `playwright` y ejecutar `playwright install chromium` en el entorno que vaya a correr contra la DGII real.
- Cargar `DGII_PORTAL_USERNAME` y `DGII_PORTAL_PASSWORD` por variables de entorno o secret manager.
- Ajustar selectores y flujos finos con una sesion manual supervisada sobre las vistas reales que se quieran cubrir.
