# Runbook Operador n8n (Autoasistido)

1. Validar que API interna y DB esten arriba.
2. Levantar n8n con `automation/n8n/docker-compose.n8n.yml`.
3. Importar workflow `dgii_postulacion_autoasistida_v1`.
4. Lanzar webhook con payload de intake.
5. Consultar progreso:
   - `GET /progress`
6. Si fallo bloqueado:
   - resolver accion humana,
   - ejecutar `POST /resume`,
   - continuar flujo en n8n.
7. Para cierre:
   - ejecutar `submit-test-ecf`,
   - ejecutar `track-status/poll`,
   - validar transicion final.
