Fecha: 2026-03-19

Validaciones ejecutadas:
- `.\.venv312\Scripts\python.exe -m pytest tests\test_chat_memory.py -q`
  - resultado: `6 passed`
- smoke CLI sobre transcript de muestra:
  - `.\.venv312\Scripts\python.exe scripts\automation\save_chat_history.py --input-file <temp>\chat_memory_sample.md --title "Smoke chat memory" --repo-root <temp>\chat_memory_repo --docs-root <temp>\chat_memory_repo\docs\prompts`
  - resultado:
    - `session_log` generado
    - `docs_prompt` generado
    - `prompt_catalog.json` generado
    - `LONG_TERM_PROMPT_MEMORY.md` generado

Cobertura validada:
- redacción de secretos
- normalización básica del prompt
- descarte de prompts triviales
- persistencia idempotente
- descubrimiento local mediante `CHAT_HISTORY_DISCOVERY_ROOTS`
- ejecución del CLI con `--input-file`
- roundtrip de codificación compacta por diccionario
- catálogo sin duplicar texto completo de prompts
- archivo compacto de sesión con referencias indexadas
