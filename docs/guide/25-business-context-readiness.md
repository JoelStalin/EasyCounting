# 25. Auditoría de herramientas del contexto de negocio

Esta guía verifica que el repositorio no solo tenga documentación comercial, sino también las herramientas operativas mínimas para sostenerla.

## Objetivo

El verificador comprueba la presencia de artefactos críticos en estas áreas:

- contexto de negocio y pricing
- memoria conversacional y cumplimiento de prompts
- demo comercial y canal de socios
- integración empresarial con Odoo
- mensajería por correo
- runbooks y documentos de compliance
- automatización DGII asistida

## Script de verificación

```powershell
python scripts/automation/check_business_context_readiness.py --repo-root C:\Users\yoeli\Documents\dgii_encf --write-report
```

## Resultado esperado

- `compliant`: existen todas las herramientas requeridas por el manifiesto actual
- `missing_tools`: faltan artefactos requeridos

## Reporte

Si usas `--write-report`, el script deja un reporte machine-readable en:

```text
.ai_context/notes/business_context_readiness_report.json
```

## Qué valida

El manifiesto actual exige, como mínimo:

- auditoría maestra de negocio y pricing
- guías de planes y monetización
- política de memoria conversacional
- catálogo y diccionario de prompts
- scripts de cierre y cumplimiento de memoria
- scripts de demo y seed comercial
- portal corporativo y portal de socios
- API empresarial Odoo y guías asociadas
- servicio SMTP y sus pruebas
- runbooks y documentos críticos de compliance
- base de automatización DGII y sus pruebas

## Notas

- El script valida existencia y cobertura mínima, no garantiza por sí solo que cada integración externa esté cerrada en producción.
- Si una nueva regla comercial pasa a ser obligatoria, debe añadirse al manifiesto en `app/business_context/readiness.py`.
