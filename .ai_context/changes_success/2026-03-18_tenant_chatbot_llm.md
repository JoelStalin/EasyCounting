# Tenant Chatbot LLM - 2026-03-18

## Objetivo

Agregar un asistente tipo chatbot para que cada usuario tenant pueda hacer preguntas sobre sus facturas y comprobantes sin acceso a informacion de otras empresas.

## Backend implementado

- endpoint `POST /api/v1/cliente/chat/ask`
- servicio `app/application/tenant_chat.py`
- aislamiento estricto por `tenant_id` extraido del JWT
- fuentes permitidas:
  - `Invoice` del tenant autenticado
- motores soportados:
  - `local`
  - `openai_compatible`
- fallback automatico al motor local si falla el proveedor externo

## Seguridad aplicada

- las consultas SQL filtran siempre por `Invoice.tenant_id == tenant_id`
- cuentas `platform_*` reciben `403` en el endpoint del chatbot
- si el usuario pregunta por un eNCF explicito que no pertenece a su tenant, la respuesta indica que no existe en su alcance
- el prompt del proveedor externo restringe la respuesta al contexto del tenant autenticado

## Frontend agregado

- `frontend/apps/client-portal/src/pages/Assistant.tsx`
- `frontend/apps/client-portal/src/api/chat.ts`
- ruta `/assistant`
- item de navegacion `Asistente`

## Verificacion

- `.\.venv\Scripts\python -m pytest tests\test_client_chat.py -q`
  - resultado: `3 passed`
- `.\.venv\Scripts\python -m pytest tests\test_client_chat.py tests\test_odoo_local_directory.py tests\test_dgii_rnc_web_parser.py -q`
  - resultado: `9 passed`

## Limitacion actual del host

- el frontend cliente quedo integrado en `src/`, pero no fue recompilado a `dist`
- en este host no hay `node` ni `pnpm` disponibles en `PATH`, por lo que el build no se pudo ejecutar desde esta sesion
