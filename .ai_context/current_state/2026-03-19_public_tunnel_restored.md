# Estado actual: túnel público restaurado

Fecha: 2026-03-19

## Problema reportado

- `cliente.getupsoft.com.do/login` mostraba `Cloudflare Tunnel error 1033`.
- El borde público dejó de tener un conector activo.
- `socios.getupsoft.com.do` además tenía una regla de ingress incorrecta apuntando a `127.0.0.1:18184`.
- `www.getupsoft.com.do` no existía todavía en DNS de Cloudflare.

## Causa raíz confirmada

1. `cloudflared` no estaba conectado al túnel `getupsoft-local` (`80297212-52f4-4f4e-b0dd-11bcd2307399`).
2. La configuración activa en `C:\Users\yoeli\.cloudflared\config.yml` estaba desalineada con la versión correcta versionada en el repo.
3. El hostname `www.getupsoft.com.do` no tenía ruta DNS al túnel.

## Correcciones aplicadas

- Se corrigió `C:\Users\yoeli\.cloudflared\config.yml`:
  - `socios.getupsoft.com.do` -> `http://127.0.0.1:18084`
  - `www.getupsoft.com.do` -> `http://127.0.0.1:18085`
- Se reinició `cloudflared` con la configuración corregida.
- Se confirmó el túnel con 4 conexiones activas.
- Se publicó `www.getupsoft.com.do` con:
  - `cloudflared tunnel route dns 80297212-52f4-4f4e-b0dd-11bcd2307399 www.getupsoft.com.do`
- Se endureció el portal de socios para que el selector de clientes no aparezca hasta que la cartera asignada haya cargado.

## Estado operativo verificado

- `https://api.getupsoft.com.do/healthz` -> `200`
- `https://admin.getupsoft.com.do/login` -> `200`
- `https://cliente.getupsoft.com.do/login` -> `200`
- `https://socios.getupsoft.com.do/login` -> `200`
- `https://getupsoft.com.do/` -> `301` hacia `https://www.getupsoft.com.do/`
- `https://www.getupsoft.com.do/` -> `200` validado contra Cloudflare con `--resolve`

## Nota operativa

- El resolver DNS por defecto de esta máquina siguió devolviendo `NXDOMAIN` para `www.getupsoft.com.do` incluso después de crear el registro.
- `1.1.1.1` y `8.8.8.8` ya resolvieron correctamente el hostname.
- El edge de Cloudflare respondió `200` para `www` cuando se forzó la resolución al IP del edge, por lo que el cambio ya quedó publicado y depende de propagación/caché del resolver local.

## Archivos implicados

- `C:\Users\yoeli\.cloudflared\config.yml`
- `frontend/apps/seller-portal/src/pages/EmitECF.tsx`
- `frontend/apps/seller-portal/src/pages/EmitECF.js`
- `frontend/apps/seller-portal/dist/`

