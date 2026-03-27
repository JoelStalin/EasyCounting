# Flujo End-to-End Autoasistido DGII

Secuencia objetivo:

1. `INTAKE_RECEIVED`
2. `PRECHECK_OK`
3. `EXPEDIENTE_LISTO`
4. `PORTAL_LOGIN`
5. `FORM_COMPLETADO`
6. `ADJUNTOS_CARGADOS`
7. `HUMAN_APPROVAL_PENDING` (si aplica)
8. `SUBMIT_DONE`
9. `TRACKID_CAPTURED`
10. `POLLING_STATUS`
11. `DONE` o `FAILED`

Integraciones:

- API interna `certificate-workflow` para estado, checkpoint y reanudacion.
- Runner dual-stack `run_portal_task` para Selenium/Playwright.
- n8n como orquestador principal.
