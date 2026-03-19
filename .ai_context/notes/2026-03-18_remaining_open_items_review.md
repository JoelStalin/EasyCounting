# Revision de Puntos Inconclusos Reales - 2026-03-18

Esta lista consolida lo que sigue pendiente despues del cierre de pruebas y despliegue del 18 de marzo de 2026.

## P0 - Bloqueos operativos actuales

1. Corregir HTTPS/TLS de Cloudflare para:
   - `api.getupsoft.com.do`
   - `admin.getupsoft.com.do`
   - `cliente.getupsoft.com.do`

2. Revisar reglas del edge/WAF de Cloudflare que hoy devuelven `403 error code: 1010` en `POST` scripted sobre los hosts del portal.

3. Instalar `cloudflared` como servicio persistente del sistema.
   Hoy sigue corriendo como proceso de usuario.

4. Repetir Selenium sobre hostnames publicos reales una vez quede resuelto el punto TLS.
   Hoy la evidencia estable quedo cerrada sobre same-origin local con backend real.

## P0 - Backend funcional aun incompleto

5. Sustituir el placeholder activo de `app/api/routes/ri.py`.
   Estado actual:
   - `GET /ri/render` -> `{\"detail\": \"RI rendering pending\"}`
   - `POST /ri/render` -> `{\"html\": \"<html></html>\", \"qr_base64\": \"\"}`

6. Decidir si `app/ri/router.py` debe reemplazar la ruta placeholder actual en `app/main.py`.

## P1 - Producto / portales

7. Implementar tutoriales autoguiados dentro de los portales.
   Estado: no existe centro de ayuda/tour embebido en runtime.

8. Implementar portal de socios (`partner-portal`).
   Estado: no existe app final para socios.

9. Implementar backend y permisos para socios:
   - `partner_reseller`
   - `partner_operator`
   - `partner_auditor`

10. Ejecutar pruebas funcionales y de permisos para el portal de socios una vez exista.

## P1 - DGII / certificacion real

11. Cerrar proceso real DGII como emisor y, si aplica, como PSFE.
   Estado: no completado oficialmente ante DGII.

12. Cargar `.p12` real y ejecutar evidencia `PRECERT/CERT`.
   Estado: pendiente por secretos reales y por sesion asistida.

13. Completar el flujo oficial de:
   - semilla
   - token
   - recepcion
   - consulta de estado
   - trackId
   - aprobacion/rechazo comercial
   - declaracion jurada

14. Automatizar o guiar con evidencia el envio/publicacion de reportes DGII `606/607/608/609`.
   Estado actual: generacion identificada en Odoo/Chefalitas, pero no envio oficial end-to-end cerrado.

## P1 - Odoo

15. Implementar `odoo_integration` runtime real para sync con Odoo 19.
   Falta:
   - sync de tenants
   - sync de invoices
   - puente JSON-RPC/servicio

16. Reescribir `getupsoft_l10n_do_pos` a Odoo 19/OWL.
   Estado conocido: sigue `installable = False`.

17. Resolver TODO/FIXME funcionales en `integration/odoo/getupsoft_do_localization`.
   Areas visibles por inspeccion:
   - `getupsoft_l10n_do_accounting`
   - `getupsoft_l10n_do_accounting_report`
   - `getupsoft_l10n_do_pos`

18. Mantener o depurar el snapshot legacy `integration/odoo/neo_do_localization`.
   Hoy sigue coexistiendo con el arbol refactorizado y arrastra TODOs antiguos.

## P2 - Calidad / hardening

19. Normalizar el worktree.
   Hay una gran cantidad de cambios previos y no pertenecen solo a este cierre.

20. Consolidar la estrategia `src/*.ts(x)` vs `src/*.js` generados.
   El repo aun convive con ambos en portales admin y cliente.

21. Estabilizar y limpiar la capa Docker/WSL.
   Ya existe evidencia de inestabilidad previa en `.ai_context/known_issues/2026-03-18_wsl_docker_instability.md`.

22. Revisar CI/workflows para que build frontend, backend y E2E queden reproducibles sin depender de pasos manuales locales.

23. Revisar secretos/defaults antes de un entorno realmente productivo:
   - bootstrap admin
   - JWT secret
   - llaves DGII
   - llaves LLM
   - observabilidad

