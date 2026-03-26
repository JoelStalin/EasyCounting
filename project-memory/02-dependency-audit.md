# Dependency Audit

## Esenciales y bien usadas

- `fastapi`, `starlette`, `sqlalchemy`, `alembic`
- `httpx` para DGII y Odoo
- `signxml`, `cryptography`, `lxml` para firma y XML
- `prometheus-fastapi-instrumentator`, `sentry-sdk`
- `pytest`, `pytest-asyncio`, `fakeredis`

## Esenciales pero mal usadas al inicio

- `alembic`: el metadata actual tenía tablas y columnas sin migración formal.
- `httpx`: el cliente DGII real coexistía con rutas fake montadas primero.
- `sqlalchemy`: el stream SSE usaba la fábrica global en lugar de respetar la sesión de prueba.

## Ausentes o incompletas para la operación actual

- `aiosqlite` no está disponible en `.venv312`, por lo que el autogenerate de Alembic contra SQLite async no funcionó en auditoría local.
- Playwright está en `requirements-dev.txt`, no en `requirements.txt`; browser automation queda fuera del runtime por defecto y se habilita solo por build arg/TEST.

## Presentes pero con riesgo operativo

- Compat layer DGII en `app/api/routes/dgii.py`: útil para compatibilidad, riesgosa si se monta antes que las rutas reales.

## Candidatas a control estricto

- `playwright`, `selenium`: solo bajo flags y en `TEST/CERT`.
- `sentry-sdk`: mantener apagado sin DSN válido.

## Conclusión

La base de dependencias es suficiente para el endurecimiento actual. El mayor gap no era la ausencia de librerías, sino el uso inconsistente del stack ya presente.
