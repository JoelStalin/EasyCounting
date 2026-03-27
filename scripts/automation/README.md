# Scripts de automatizacion

Este directorio esta reservado para scripts de automatizacion del proyecto.

Uso sugerido:

- utilidades de Selenium y E2E
- helpers de smoke/regresion
- scripts de bootstrap para QA local
- arranque seguro en WSL con puertos solo en `127.0.0.1`
- automatizacion Route53 con perfil IAM dedicado o credenciales temporales
- corrida Selenium visual con navegador real y reporte HTML
- runbooks operativos para certificacion controlada

Nuevos scripts para onboarding de certificado DGII:

- `certificate_workflow_cli.py`: intake + precheck + expediente por `case_id`.
- `validate_dgii_p12.py`: validacion tecnica automatica de `.p12/.pfx` en JSON.
