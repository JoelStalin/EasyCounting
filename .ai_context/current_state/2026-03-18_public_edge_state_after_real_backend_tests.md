# Estado Publico del Edge y Servicios - 2026-03-18

## Resumen ejecutivo

El proyecto quedo operativo en esta maquina con `cloudflared` activo y con el borde publico resolviendo por HTTP para:

- `http://api.getupsoft.com.do`
- `http://admin.getupsoft.com.do`
- `http://cliente.getupsoft.com.do`
- `http://getupsoft.com.do` -> `301` hacia `http://admin.getupsoft.com.do/`

Tambien quedaron levantados dos grupos de orígenes locales:

- borde publico local:
  - `127.0.0.1:18081` admin
  - `127.0.0.1:18082` cliente
  - `127.0.0.1:18083` redirect apex
- arnes local same-origin para pruebas reales contra backend:
  - `127.0.0.1:18181` admin
  - `127.0.0.1:18182` cliente
  - `127.0.0.1:18183` redirect apex

Backend y tunel en el momento del cierre:

- `cloudflared` PID `11548`
- metricas `127.0.0.1:20241`
- API/nginx local `127.0.0.1:28080`
- Docker:
  - `dgii_encf-web-1` healthy
  - `dgii_encf-nginx-1` up
  - `dgii_encf-db-1` healthy
  - `dgii_encf-redis-1` up

## Validaciones publicas cerradas

Se confirmo por HTTP:

- `http://api.getupsoft.com.do/healthz` -> `200`
- `http://admin.getupsoft.com.do/login` -> `200`
- `http://cliente.getupsoft.com.do/login` -> `200`
- `http://getupsoft.com.do/` -> `301` a `http://admin.getupsoft.com.do/`

Los bundles publicos servidos ya corresponden al build corregido del 18 de marzo:

- `last-modified: Thu, 19 Mar 2026 02:24:06 GMT` en `admin` y `cliente`

## Cambios tecnicos relevantes aplicados

- Se corrigio el frontend para autenticar contra rutas versionadas reales:
  - `/api/v1/auth/login`
  - `/api/v1/me`
- Se regeneraron `dist` de:
  - `frontend/apps/admin-portal`
  - `frontend/apps/client-portal`
- `serve_spa.py` ahora soporta proxy same-origin hacia el backend para:
  - `/api`
  - `/ri`
  - `/receptor`
  - `health/readiness`
- `start_local_public_edge.ps1` ahora puede levantar admin y cliente con:
  - `runtime-api-base-url` por host
  - `proxy-api-base-url` al backend real

## Bloqueos vigentes

### 1. HTTPS publico aun no usable

Las tres URLs HTTPS siguen fallando desde este host con:

- `SEC_E_ILLEGAL_MESSAGE`
- `ERR_SSL_VERSION_OR_CIPHER_MISMATCH`

Afecta:

- `https://api.getupsoft.com.do/healthz`
- `https://admin.getupsoft.com.do/login`
- `https://cliente.getupsoft.com.do/login`

### 2. Cloudflare edge devuelve `1010` para `POST` scripted sobre hosts de portal

Se observo `403 error code: 1010` al hacer `POST` no navegador a:

- `http://admin.getupsoft.com.do/api/v1/auth/login`
- `http://cliente.getupsoft.com.do/api/v1/auth/login`

El mismo `POST` funciona correctamente:

- directo a `127.0.0.1:28080`
- same-origin local a `127.0.0.1:18082/api/v1/auth/login`

Esto apunta a una regla del edge/WAF de Cloudflare sobre los hosts publicos del portal, no al backend FastAPI.

### 3. `cloudflared` corre como proceso de usuario, no como servicio persistente

La instalacion como servicio Windows no se pudo completar por permisos del `Service Control Manager`. El tunel sigue arriba, pero no quedo endurecido como servicio del sistema.

