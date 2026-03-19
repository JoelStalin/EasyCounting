Fecha: 2026-03-19

Validación ejecutada:
- `.\.venv312\Scripts\python.exe -m pytest tests\test_client_chat.py tests\test_admin_ai_providers.py -q`
  - resultado: `7 passed`

Cobertura validada:
- el chatbot local sigue respondiendo preguntas tenant-scoped
- el proveedor IA por defecto sigue usándose para preguntas analíticas
- las preguntas operativas evitan el proveedor externo aunque exista uno configurado
- la respuesta incluye metadatos de preproceso:
  - intención detectada
  - estrategia de despacho
  - indicador de ahorro de créditos

Limitación:
- no se pudo ejecutar build del portal cliente en esta shell porque `node`, `corepack` y `pnpm` no están disponibles en `PATH`
