## Estado actual

- Fecha: 2026-03-18
- Objetivo: publicar `getupsoft.com.do` usando `Cloudflare` y completar el corte DNS desde `cp.midominio.do`.

## Hechos confirmados

- `cp.midominio.do` acepta el acceso del cliente y el dominio `getupsoft.com.do` existe en la cuenta.
- El detalle del dominio quedó identificado en:
  - `artifacts_live_dns/cp_midominio_jump_direct.html`
  - `artifacts_live_dns/cp_midominio_manage_ns_modal.html`
- El formulario correcto para reemplazar los nameservers está en `Administrar Nombre de Servidores`.
- Los nameservers actuales del dominio son:
  - `ns-1304.awsdns-35.org`
  - `ns-1941.awsdns-50.co.uk`
  - `ns-432.awsdns-54.com`
  - `ns-758.awsdns-30.net`
- `Cloudflare` sigue bloqueado por verificación humana en el login web.

## Restricción operativa

- No se intentará evadir ni automatizar el challenge anti-bot de Cloudflare.
- El próximo paso requiere intervención humana breve: completar el challenge en el navegador visible y dejar entrar al dashboard.

## Próximo paso

1. Completar verificación humana de Cloudflare.
2. Crear o localizar la zona `getupsoft.com.do`.
3. Capturar los nameservers asignados por Cloudflare.
4. Volver a `cp.midominio.do` y reemplazar los 4 nameservers actuales.
5. Continuar con `cloudflared tunnel` y publicación de `api/admin/cliente`.
