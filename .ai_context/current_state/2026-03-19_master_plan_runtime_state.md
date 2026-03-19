# Estado runtime master plan

Fecha de cierre: 2026-03-19

## Servicios activos

- API principal: `http://127.0.0.1:28080/healthz` -> `200`
- Admin portal: `http://127.0.0.1:18081/login` -> `200`
- Client portal: `http://127.0.0.1:18082/login` -> `200`
- Seller portal: `http://127.0.0.1:18084/login` -> `200`
- Corporate portal: `http://127.0.0.1:18085/` -> `200`
- Odoo 19 lab Chefalitas: `http://127.0.0.1:19069/web/login` -> `200`

## Contenedores confirmados

- `dgii_encf-db-1` -> `Up (healthy)`
- `dgii_encf-redis-1` -> `Up`
- `dgii_encf-web-1` -> `Up (healthy)`
- `dgii_encf-nginx-1` -> `Up`
- `dgii_encf-web_demo-1` -> `Up (healthy)`

## Componentes cerrados en esta fase

- Social auth backend y frontend para `google`, `facebook` y `apple`.
- MFA basado en `challengeId` con compatibilidad hacia el flujo anterior.
- Persistencia backend de tours por vista y por usuario.
- Tours autoguiados con primer disparo y relanzamiento manual en admin, client y seller.
- Servicio SMTP modular con configuracion por entorno, adjuntos y script de prueba.
- Portal corporativo `corporate-portal` con secciones:
  - `/`
  - `/productos`
  - `/productos/accounting-management`
  - `/plataforma`
  - `/contacto`
- Correccion de la ruta publica `RI` para usar el router real.
- Seller portal mantenido y endurecido sobre el baseline existente.
- Edge local ampliado para `www/corporate`, `admin`, `cliente`, `socios` y `api`.

## Estado operativo relevante

- La API ya autentica usuarios demo reales en la base levantada por Docker.
- Los portales ya no intentan autenticarse contra `127.0.0.1` cuando el runtime-config usa hostnames publicos.
- El helper Selenium ya interactua correctamente con `react-joyride` usando los controles reales del DOM del tour.
- El entorno Python operativo para validacion local es `.venv312`.

## Riesgos abiertos

- `cloudflared` sigue como proceso de usuario y no como servicio persistente del sistema.
- La certificacion real DGII `PRECERT/CERT/PROD` sigue fuera de automatizacion y requiere ejecucion asistida.
- El bridge runtime vivo con Odoo sigue siendo trabajo posterior.
