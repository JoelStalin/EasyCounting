# Estado integral del runtime

Fecha base: 2026-03-18  
Última validación operativa: 2026-03-19 UTC

## Servicios principales levantados

### Stack principal
- API local: `http://127.0.0.1:28080/healthz` -> `200`
- Admin local: `http://127.0.0.1:18081/login` -> `200`
- Cliente local: `http://127.0.0.1:18082/login` -> `200`
- Seller local: `http://127.0.0.1:18084/login` -> `200`

### Stack demo independiente
- API demo: `http://127.0.0.1:28180/healthz` -> `200`
- Admin demo: `http://127.0.0.1:18181/login` -> `200`
- Cliente demo: `http://127.0.0.1:18182/login` -> `200`
- Seller demo: `http://127.0.0.1:18184/login` -> `200`

### Laboratorio Odoo 19
- Odoo Chefalitas lab: `http://127.0.0.1:19069/web/login` -> `200`
- Base del laboratorio: `chefalitas19lab`
- Puerto PostgreSQL del lab: `55439`

### Edge público
- Túnel activo: `getupsoft-local`
- Tunnel ID: `80297212-52f4-4f4e-b0dd-11bcd2307399`
- Proceso `cloudflared`: PID `6308`
- Config activa local: `C:\Users\yoeli\.cloudflared\config.yml`

## Hostnames públicos validados

- `https://admin.getupsoft.com.do`
- `https://cliente.getupsoft.com.do`
- `https://socios.getupsoft.com.do`
- `https://api.getupsoft.com.do`
- `https://getupsoft.com.do` redirige al admin

La validación pública funcional se cerró en navegador real con Selenium sobre Chrome y Edge.

## Contenedores relevantes activos

- `dgii_encf-web-1`
- `dgii_encf-nginx-1`
- `dgii_encf-web_demo-1`
- `dgii_encf-db-1`
- `dgii_encf-redis-1`
- `odoo19_chefalitas-odoo-1`
- `odoo19_chefalitas-db-1`

## Hallazgos operativos cerrados en esta fase

- Seller público corregido: el host `socios.getupsoft.com.do` ya resuelve y autentica contra el backend demo correcto.
- Runtime frontend endurecido: los portales ya no intentan usar `127.0.0.1` cuando el origen real es un dominio público.
- Warnings de Compose: removida la clave `version` obsoleta en los compose del repo.
- Warnings Odoo 19: migrados los `UNIQUE` críticos a `models.Constraint`.
- Warning Odoo de `http_interface`: corregido en `labs/odoo19_chefalitas/odoo.conf`.

## Hallazgos operativos aún abiertos

- `cloudflared` sigue corriendo como proceso de usuario, no como servicio persistente del sistema.
- Sigue existiendo ruido externo del contenedor heredado `jabiya15local-queue_consumer-1`; no forma parte del baseline aceptado de esta fase.
- El laboratorio Odoo funciona fiscalmente, pero el `chart_template` sigue quedando en `generic_coa` en el bootstrap limpio.
