# Contexto consolidado de ejecución integral

## Objetivo ejecutado

Implementar el plan integral para:

- laboratorio Odoo 19 basado en `Chefalitas`
- cierre de pendientes reales del backend y edge
- ambiente demo independiente
- portal de revendedores / sellers
- checklist final y evidencia auditada

## Cambios materiales cerrados en esta ronda

### Frontend / edge
- Corregida la resolución del API base URL en:
  - `frontend/apps/admin-portal/src/api/client.ts`
  - `frontend/apps/client-portal/src/api/client.ts`
  - `frontend/apps/seller-portal/src/api/client.ts`
  - equivalentes `.js`
- Resultado:
  - los portales ya usan origen público correcto detrás del túnel
  - queda corregido el fallo seller público que intentaba hablar con `127.0.0.1`

### Odoo 19 / localización
- Bootstrap reproducible del laboratorio desde:
  - `scripts/automation/odoo19_chefalitas/bootstrap_lab.ps1`
  - `scripts/automation/odoo19_chefalitas/provision_lab_odoo.py`
- Compatibilidad Odoo 19 cerrada en:
  - `getupsoft_l10n_do_accounting`
  - `getupsoft_l10n_do_accounting_report`
- Warnings de `UNIQUE` migrados a `models.Constraint`

### Infra / compose
- Eliminada la clave `version` de:
  - `docker-compose.yml`
  - `deploy/docker-compose.yml`
- `labs/odoo19_chefalitas/odoo.conf` actualizado con `http_interface = 0.0.0.0`

## Pruebas ejecutadas en esta ronda

- Backend crítico: `10 passed`
- Selenium público Chrome: `4 passed`
- Selenium público Edge: `4 passed`
- Validación de servicios locales y demo: todos `200`
- Validación Odoo: login `200`, factura posteada, reporte DGII generado

## Resultado operativo

El proyecto quedó accesible y demostrable en:

- `https://admin.getupsoft.com.do`
- `https://cliente.getupsoft.com.do`
- `https://socios.getupsoft.com.do`

con un stack demo independiente y un laboratorio Odoo 19 funcional.

## Riesgos remanentes documentados

- go-live fiscal real DGII no ejecutado
- persistencia del túnel no endurecida como servicio de sistema
- bridge vivo con Odoo aún pendiente
- chart template dominicano limpio aún pendiente en bootstrap
