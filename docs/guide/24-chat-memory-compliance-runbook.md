# 24. Runbook de cierre de memoria conversacional

Usa este flujo cada vez que cierres una sesión de trabajo en `dgii_encf`.

## Flujo diario

1. Trabaja normalmente en el repo.
2. Exporta el transcript del chat o asegúrate de que pueda descubrirse localmente.
3. Ejecuta el cierre obligatorio:

```powershell
python scripts/automation/close_project_chat_session.py --discover-local --title "Cierre de sesión"
```

4. Si no existe un transcript local usable, pásalo por archivo o `stdin`:

```powershell
python scripts/automation/close_project_chat_session.py --input-file C:\ruta\conversation.md --title "Cierre de sesión"
```

5. Verifica el cumplimiento:

```powershell
python scripts/automation/check_chat_memory_compliance.py
```

## Criterio de cierre correcto

Una sesión se considera cerrada correctamente cuando:

- existe el archivo `*_session.md`
- existe el archivo `*_session.compact.json`
- existe la copia en `docs/prompts`
- `LONG_TERM_PROMPT_MEMORY.md` contiene el bloque de la sesión
- `prompt_catalog.json` referencia la sesión
- el verificador devuelve `compliant`

## Notas

- La política se activa automáticamente dentro de este repo.
- No guardes secretos en texto plano: el flujo redacta, pero no reemplaza una buena higiene operativa.
- Si el verificador no devuelve `compliant`, la sesión debe considerarse incompleta.
