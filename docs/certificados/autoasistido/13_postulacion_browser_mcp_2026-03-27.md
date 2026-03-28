# 13 - Postulación DGII con Browser MCP (2026-03-27)

## Objetivo
Migrar la postulación real como emisor electrónico al nuevo runtime `browser-mcp` y validar el flujo hasta la carga del XML firmado.

## Resultado
- Flujo completado hasta:
  - login OFV,
  - apertura de postulación,
  - generación de XML,
  - firma local con `.p12`,
  - carga del XML firmado.
- Respuesta actual del portal:
  - `Error XML. Firma Inválida.`

## Evidencia principal
- Carpeta del run:
  - `tests/artifacts/2026-03-27_19-06-49_dgii_postulacion_browser_mcp/`
- Resumen:
  - `tests/artifacts/2026-03-27_19-06-49_dgii_postulacion_browser_mcp/run-summary.json`
- Pantallas clave:
  - `ofv_authenticated.png`
  - `filled_postulacion.png`
  - `generated_postulacion.png`
  - `signed_xml_selected.png`
  - `after_signed_upload.png`

## XML y firma usados
- XML generado:
  - `202603270731754.xml`
- XML firmado:
  - `202603270731754.signed.xml`
- Modo de firma registrado:
  - `signed_with_local_p12:register_http_400`

## Hallazgo operativo
- El nuevo flujo `browser-mcp` reproduce el comportamiento observado previamente con Selenium:
  - la navegación y carga sí funcionan;
  - el bloqueo real queda en la aceptación de la firma del XML por DGII.

## Código introducido para este flujo
- Sidecar/browser scenarios:
  - `automation/browser-mcp/src/scenarios/dgii/shared.ts`
  - `automation/browser-mcp/src/scenarios/dgii/postulacion-generate-xml.ts`
  - `automation/browser-mcp/src/scenarios/dgii/postulacion-upload-signed-xml.ts`
- Orquestación Python:
  - `app/services/browser_mcp/dgii_postulacion.py`
  - `scripts/automation/run_real_dgii_postulacion_browser_mcp.py`

## Siguiente paso recomendado
1. Validar por qué la firma del XML firmado no es aceptada por DGII:
   - identidad del certificado vs representante registrado,
   - estructura exacta del XML firmado,
   - canonicalización/reference/digest,
   - diferencias entre el XML firmado actual y el XML que el portal espera para postulación.
