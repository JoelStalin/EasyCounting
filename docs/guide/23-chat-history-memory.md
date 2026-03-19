# 23. Memoria conversacional del repositorio

Esta guía describe cómo guardar conversaciones útiles del chat dentro del repositorio para que otro agente IA pueda recuperar contexto, errores, decisiones y pendientes sin depender de memoria externa.

## Objetivo

La herramienta:

- importa transcripts desde archivo, `stdin` o descubrimiento local
- sanea secretos antes de persistir
- corrige ortografía y claridad básica en una versión normalizada
- separa prompts útiles del ruido trivial
- actualiza memoria operativa en `.ai_context`
- genera una copia legible en `docs/prompts`

## Política automática del repo

Dentro de `C:\Users\yoeli\Documents\dgii_encf` se activa una política obligatoria de memoria conversacional:

- el cierre de sesión se considera obligatorio
- siempre se guarda transcript saneado y transcript normalizado
- siempre se actualizan `LONG_TERM_PROMPT_MEMORY.md`, `prompt_catalog.json` y `prompt_dictionary.json`
- siempre se genera la copia en `docs/prompts`
- el estado de la política queda persistido en `.ai_context/notes/chat_memory_policy.json`

Si el CLI se ejecuta dentro de este repositorio, la política se activa automáticamente aunque no pases `--close-session`.

## Script principal

```powershell
python scripts/automation/save_chat_history.py --input-file C:\ruta\conversation.md --title "Cierre de sesión"
```

También soporta:

```powershell
python scripts/automation/save_chat_history.py --stdin --title "Transcript pegado"
python scripts/automation/save_chat_history.py --discover-local --title "Transcript descubierto"
python scripts/automation/save_chat_history.py --input-file C:\ruta\conversation.json --title "Sesión"
```

## Cierre obligatorio del proyecto

Para el flujo diario del repo usa:

```powershell
python scripts/automation/close_project_chat_session.py --discover-local --title "Cierre del día"
```

Ese comando:

- importa el transcript
- fuerza el modo de cierre
- persiste todos los artefactos obligatorios
- ejecuta la verificación de cumplimiento al final

## Verificación de cumplimiento

```powershell
python scripts/automation/check_chat_memory_compliance.py
```

Estados esperados:

- `compliant`
- `missing_session_archive`
- `missing_memory_update`
- `missing_docs_copy`
- `missing_catalog_entry`

## Salidas

Cada corrida actualiza:

- `.ai_context/session_logs/YYYY-MM-DD_<slug>_session.md`
- `.ai_context/session_logs/YYYY-MM-DD_<slug>_session.compact.json`
- `.ai_context/notes/LONG_TERM_PROMPT_MEMORY.md`
- `.ai_context/notes/prompt_catalog.json`
- `.ai_context/notes/prompt_dictionary.json`
- `.ai_context/notes/chat_memory_policy.json`
- `docs/prompts/YYYY-MM-DD_<slug>.md`

## Qué guarda

Por cada prompt útil:

- prompt original saneado
- versión normalizada y amigable para IA
- resumen del resultado del asistente
- errores o brechas detectadas
- solución o decisión tomada
- estado
- pendientes
- archivos o evidencia
- etiquetas
- sensibilidad

Además, la fuente canónica legible por máquina se guarda de forma compacta:

- diccionario global de tokens en `.ai_context/notes/prompt_dictionary.json`
- sesión compacta con referencias indexadas en `.ai_context/session_logs/*.compact.json`

De esta forma, palabras y fragmentos repetidos no se vuelven a guardar completos en cada entrada del catálogo.

## Seguridad

La herramienta redacta automáticamente:

- contraseñas
- tokens
- cookies
- claves API
- bloques PEM
- correos electrónicos
- identificadores fiscales cuando aparecen como datos sensibles

No debes usarla como repositorio de secretos. Si el transcript contiene credenciales, la salida persistida solo conservará versiones redactadas.

## Descubrimiento local

`--discover-local` intenta encontrar transcripts recientes en rutas típicas como:

- directorio actual
- `Downloads`
- `Documents`
- `~/.codex`

Si no encuentra nada, falla con un mensaje claro y te pide usar `--input-file` o `--stdin`.

## Notas operativas

- La salida normalizada no reemplaza el transcript saneado; ambas representaciones se conservan.
- El catálogo JSON no duplica el texto completo de cada prompt; apunta al archivo compacto por sesión.
- El diccionario global usa índices cortos para tokens repetidos y reduce duplicación entre sesiones.
- `LONG_TERM_PROMPT_MEMORY.md` se actualiza con bloques idempotentes por `session_id`.
- Dentro de este repo, una sesión no debe darse por cerrada sin pasar por `close_project_chat_session.py` o por `save_chat_history.py` con política activa.
