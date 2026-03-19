# 2026-03-19 - Política obligatoria de memoria conversacional

## Cambio aplicado

Se agregó una política repo-aware para `dgii_encf` sobre la infraestructura de `app/chat_memory`.

## Resultado

- el cierre de sesión queda forzado dentro del repo
- `save_chat_history.py` activa la política automáticamente
- se agregó `close_project_chat_session.py`
- se agregó `check_chat_memory_compliance.py`
- se agregó `chat_memory_policy.json`
- se documentó el flujo operativo y el runbook

## Evidencia principal

- `app/chat_memory/policy.py`
- `app/chat_memory/compliance.py`
- `scripts/automation/close_project_chat_session.py`
- `scripts/automation/check_chat_memory_compliance.py`
- `docs/guide/23-chat-history-memory.md`
- `docs/guide/24-chat-memory-compliance-runbook.md`
