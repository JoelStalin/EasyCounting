# Transicion a Infraestructura Ubuntu (WSL)

Fecha: 2026-03-19

## Novedades del Estado
- Los servicios base del sistema (SPA Servers, Docker Engine y dependencias backend) fueron apagados en el host de Windows.
- Se implemento el script puente `scripts/automation/start_wsl_edge.sh` que encendio la estructura de microservicios limpia y completamente bajo el kernel Linux del sistema usando WSL2.
- Puertos Expuestos via el `0.0.0.0` interno hacia el `127.0.0.1` de Windows:
  - 18081: Admin Portal (Vite React UI)
  - 18082: Client Portal
  - 18085: Corporate Portal
  - 28080: FastAPI Backend (API Proxy)

## Riesgo y Pruebas
- Selenium evidencio de inmediato un "timeout" en Windows a la hora de probar credenciales de Mock contra el entorno real levantado por WSL.
- En base a este reporte, el siguiente paso activo es abrir una ventanilla inyectando el componente `browser_subagent` interactuando visualmente simulando ser un usuario. Se utilizaran las credenciales reales de paso que marca el archivo `.ai_context/notes/2026-03-19_master_plan_checklist.md`: `admin@getupsoft.com.do`.
