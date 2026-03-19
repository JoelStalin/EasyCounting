## Estado actual

- Fecha: 2026-03-18
- Dominio: `getupsoft.com.do`
- Objetivo: publicación pública con `Cloudflare Tunnel` y hostnames `api/admin/cliente`.

## Cambios completados

- Se reutilizó la sesión activa de Chrome del perfil `JOEL STALIN` (`Default`) para operar `Cloudflare` sin volver a loguear.
- En `Cloudflare` se creó la zona `getupsoft.com.do` en plan `Free`.
- `Cloudflare` asignó estos nameservers:
  - `piers.ns.cloudflare.com`
  - `veronica.ns.cloudflare.com`
- En `cp.midominio.do` se reemplazaron los nameservers previos de AWS:
  - `ns-1304.awsdns-35.org`
  - `ns-1941.awsdns-50.co.uk`
  - `ns-432.awsdns-54.com`
  - `ns-758.awsdns-30.net`
- El registrador devolvió confirmación:
  - `Los datos del Servidor de Nombres se han actualizado correctamente`
- Se verificó reabriendo el modal del registrador:
  - `piers.ns.cloudflare.com`
  - `veronica.ns.cloudflare.com`
- Se autorizó `cloudflared tunnel login` y quedó generado:
  - `%USERPROFILE%\.cloudflared\cert.pem`
- Se creó el túnel nombrado:
  - `getupsoft-local`
  - `tunnel id: 80297212-52f4-4f4e-b0dd-11bcd2307399`
- Se dejó la configuración activa en:
  - `%USERPROFILE%\.cloudflared\config.yml`
  - `ops/cloudflared/getupsoft.com.do.local.yml`
- Se publicaron rutas DNS del túnel para:
  - `getupsoft.com.do`
  - `api.getupsoft.com.do`
  - `admin.getupsoft.com.do`
  - `cliente.getupsoft.com.do`
- El proceso `cloudflared tunnel run` quedó levantado y registró conexiones QUIC.

## Evidencia local

- `artifacts_live_dns/cloudflare_tunnel_authorize_window.png`
- `artifacts_live_dns/cp_midominio_before_submit_cloudflare_ns.png`
- `artifacts_live_dns/cp_midominio_after_submit_cloudflare_ns.png`
- `artifacts_live_dns/cloudflared_run.err.log`
- `artifacts_live_dns/cloudflared_login.log`

## Bloqueo actual

- `Cloudflare` todavía muestra:
  - `Waiting for your registrar to propagate your new nameservers`
- Las consultas públicas aún no resuelven desde `1.1.1.1`, por lo que la delegación del registro `.do` todavía está propagando.
- La instalación como servicio Windows falló por permisos:
  - `Cannot establish a connection to the service control manager: Access is denied.`

## Siguiente paso

1. Esperar propagación pública del cambio de nameservers.
2. Validar resolución DNS de `getupsoft.com.do`, `api`, `admin` y `cliente`.
3. Ejecutar pruebas funcionales Selenium sobre URLs públicas.
