# 2026-03-19 - Validación de política de memoria conversacional

## Pruebas automatizadas

```text
.\.venv312\Scripts\python.exe -m pytest tests\test_chat_memory.py -q
8 passed in 8.66s
```

## Validación operativa en el repo real

Bootstrap de una sesión inicial:

```text
.\.venv312\Scripts\python.exe scripts\automation\close_project_chat_session.py --input-file C:\Users\yoeli\Downloads\prompt_branding_ceo_facturacion.md --title "Bootstrap memoria conversacional"
```

Resultado:

- se generó `prompt_catalog.json`
- se generó `prompt_dictionary.json`
- se generó la sesión markdown
- se generó la sesión compacta
- se generó la copia en `docs/prompts`
- el verificador devolvió `compliant`

Chequeo final:

```text
.\.venv312\Scripts\python.exe scripts\automation\check_chat_memory_compliance.py --repo-root C:\Users\yoeli\Documents\dgii_encf
status = compliant
```
