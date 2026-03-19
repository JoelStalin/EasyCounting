Fecha: 2026-03-19

Cambio:
- Se implementó una herramienta modular para guardar y organizar historial de chat dentro del repositorio.

Componentes agregados:
- `app/chat_memory/ingest.py`
- `app/chat_memory/normalize.py`
- `app/chat_memory/classify.py`
- `app/chat_memory/redact.py`
- `app/chat_memory/persist.py`
- `app/chat_memory/cli.py`
- `scripts/automation/save_chat_history.py`
- `tests/test_chat_memory.py`
- `docs/guide/23-chat-history-memory.md`

Capacidades:
- importar transcripts desde archivo, `stdin` o descubrimiento local
- redactar secretos antes de persistir
- construir versión normalizada y amigable para IA
- separar prompts útiles del ruido trivial
- escribir sesión detallada en `.ai_context/session_logs/`
- escribir una sesión compacta en `.ai_context/session_logs/*.compact.json`
- actualizar catálogo maestro en `.ai_context/notes/prompt_catalog.json` sin duplicar texto completo
- actualizar memoria larga en `.ai_context/notes/LONG_TERM_PROMPT_MEMORY.md`
- generar copia legible en `docs/prompts/`
- mantener un diccionario global de tokens en `.ai_context/notes/prompt_dictionary.json`

Optimización agregada:
- las palabras y fragmentos repetidos ya no se guardan completos una y otra vez en el catálogo
- el almacenamiento canónico para máquina usa índices cortos por token, referenciados contra un diccionario global
- cada prompt del catálogo ahora apunta al archivo compacto de sesión en vez de copiar nuevamente el texto normalizado

Limitación actual:
- la herramienta no puede capturar por sí sola el transcript vivo del chat si el cliente no expone un archivo local accesible; en ese caso requiere `--input-file` o `--stdin`.
