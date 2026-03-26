# Browser Automation Architecture

## Alcance permitido

- Evidencia visual en `TEST/CERT`
- Navegación asistida en flujos manuales permitidos
- Respaldo operacional cuando no exista servicio web suficiente

## Guardrails

- Nunca reemplaza la verdad fiscal de DGII.
- Nunca evade CAPTCHA, MFA o rate limits.
- Siempre detrás de flags:
  - `DGII_BROWSER_AUTOMATION_ENABLED`
  - `DGII_BROWSER_AUTOMATION_MODE=assistive|fallback|evidence-only`

## Módulo implementado

- `automation/browser/config.py`
- `automation/browser/drivers/playwright_driver.py`
- `automation/browser/workflows/dgii_evidence.py`
- `automation/browser/evidence/collector.py`
- `automation/browser/tests/test_browser_feature_flags.py`
