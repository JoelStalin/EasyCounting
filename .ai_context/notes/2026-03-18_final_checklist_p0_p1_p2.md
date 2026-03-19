# Checklist final P0 / P1 / P2

## P0 cerrados

- [x] Backlog canónico consolidado con evidencia operativa.
- [x] Ruta pública de RI deja de ser placeholder y usa el router real.
- [x] Portal seller / revendedores implementado con roles:
  - `partner_reseller`
  - `partner_operator`
  - `partner_auditor`
- [x] Demo independiente preparada con base propia y credenciales dummy separadas.
- [x] Admin, client y seller compilan y publican `dist` reproducibles.
- [x] Hostnames públicos funcionales para admin, cliente y seller.
- [x] Selenium público pasa en Chrome y Edge.
- [x] Laboratorio Odoo 19 desde Chefalitas queda levantado y accesible.
- [x] Se genera factura de prueba real en Odoo y queda posteada.
- [x] Se genera reporte DGII base en Odoo lab.
- [x] Se corrigieron los warnings operativos principales del repo objetivo.

## P0 abiertos

- [ ] Certificación DGII real `PRECERT/CERT` y habilitación formal como emisor/PSFE.
  - Bloqueo: requiere ejecución fiscal/legal asistida, certificado `.p12` válido y pasos oficiales ante DGII.

## P1 abiertos

- [ ] Persistencia del edge público.
  - `cloudflared` sigue como proceso de usuario; falta convertirlo en servicio persistente del sistema o equivalente operable tras reinicio.
- [ ] Odoo lab todavía queda con `chart_template = generic_coa` en bootstrap limpio.
  - La factura y el reporte DGII ya funcionan, pero la plantilla contable dominicana no queda como baseline limpio.
- [ ] Publicación guiada/automatizada de reportes DGII `606/607/608/609` desde Odoo hacia DGII no está implementada.
- [ ] Bridge runtime `odoo_integration` para sincronización viva entre esta plataforma y Odoo sigue pendiente.
- [ ] Política completa de “3 opciones” para demo/debugger/preview privada con allowlist no quedó cerrada en esta fase.

## P2 abiertos

- [ ] Reescritura de `getupsoft_l10n_do_pos` a Odoo 19/OWL.
- [ ] Convivencia `src/*.ts(x)` y `src/*.js` en los frontends sigue siendo deuda de mantenimiento.
- [ ] Tutoriales autoguiados integrados en los portales siguen pendientes.
- [ ] Endurecimiento adicional de CI/CD y limpieza de servicios heredados ajenos al baseline.
- [ ] Ruido de contenedores legacy como `jabiya15local-queue_consumer-1` debe aislarse o retirarse del host si se quiere un entorno totalmente limpio.

## Credenciales demo entregables

- Admin demo: `admin@getupsoft.com.do / ChangeMe123!`
- Cliente demo: `cliente@getupsoft.com.do / Tenant123!`
- Seller demo: `seller@getupsoft.com.do / Seller123!`
- Seller auditor demo: `seller.auditor@getupsoft.com.do / SellerAudit123!`

## Decisión de baseline

El baseline aceptado al cierre de esta fase es:

- stack principal `dgii_encf`
- stack demo independiente
- laboratorio `labs/odoo19_chefalitas`
- edge público Cloudflare para `admin`, `cliente`, `socios` y `api`

Queda explícitamente fuera del criterio de aceptación de esta fase cualquier ruido operativo proveniente de `jabiya` o de contenedores heredados no pertenecientes al baseline anterior.
