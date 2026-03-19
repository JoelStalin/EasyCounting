Fecha: 2026-03-19

Cambio:
- Se agregó preprocesamiento centralizado para el asistente tenant-scoped antes de derivar consultas a proveedores IA externos.

Objetivo:
- normalizar preguntas del usuario
- detectar intención
- resolver consultas operativas con motor local
- evitar consumo innecesario de créditos cuando la respuesta puede salir del motor determinístico del sistema

Implementación:
- `app/application/tenant_chat.py`
  - nueva decisión de preproceso
  - detección de intención `greeting`, `operational_lookup`, `analysis`, `open_question`
  - estrategia de despacho `local_only` o `provider_preferred`
- `app/portal_client/schemas.py`
  - nuevo bloque `preprocess` en la respuesta del chat
- `frontend/apps/client-portal/src/pages/Assistant.tsx`
  - transparencia visual del preproceso aplicado

Resultado:
- preguntas operativas como estado, conteo, resumen, rechazo o detalle de comprobantes se resuelven localmente cuando hay datos suficientes
- preguntas analíticas u abiertas siguen pudiendo usar el proveedor IA configurado
- la respuesta del chat ahora informa si se evitó consumir crédito
