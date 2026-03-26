# DEC-003 Browser Automation Guardrails

- Fecha: 2026-03-25
- Tema: automatización controlada por navegador para DGII
- Fuente:
  - https://dgii.gov.do/cicloContribuyente/facturacion/comprobantesFiscalesElectronicosE-CF/Paginas/documentacionSobreE-CF.aspx
  - política operativa del proyecto registrada en este hardening
- Conclusión práctica:
  - API oficial primero.
  - Browser automation solo con feature flags y sin bypass de controles.
- Archivos afectados:
  - `automation/browser/config.py`
  - `automation/browser/workflows/dgii_evidence.py`
  - `automation/browser/tests/test_browser_feature_flags.py`
- Impacto:
  - El módulo queda encapsulado, auditable y desactivable.
