# Evidencia: restauración del borde público y pruebas funcionales

Fecha: 2026-03-19

## Verificaciones HTTP públicas

- `https://api.getupsoft.com.do/healthz` -> `200`
- `https://admin.getupsoft.com.do/login` -> `200`
- `https://cliente.getupsoft.com.do/login` -> `200`
- `https://socios.getupsoft.com.do/login` -> `200`
- `https://getupsoft.com.do/` -> `301` a `https://www.getupsoft.com.do/`
- `https://www.getupsoft.com.do/` -> `200` usando `curl --resolve`

## Estado del túnel

- Túnel: `getupsoft-local`
- ID: `80297212-52f4-4f4e-b0dd-11bcd2307399`
- Conector activo:
  - `f5f4a0c8-a729-4012-9f53-975cf9c178e4`
- Edge activos informados por `cloudflared tunnel info`:
  - `1xmia01`
  - `1xmia02`
  - `1xmia04`
  - `1xmia07`

## Suite funcional pública

Artefacto:

- `e2e/artifacts/public_fix_retry_20260319_155543/report.html`

Resultado consolidado del reporte:

- `4 Passed`
- `0 Failed`
- `0 Errors`

Cobertura:

- admin:
  - login
  - vista `Agentes IA`
  - creación de compañía
  - detalle de compañía
- cliente:
  - login
  - emisión demo e-CF
  - perfil
  - logout
- socios:
  - login reseller
  - emisión demo
  - clientes asignados
  - perfil
  - logout
  - validación de denegación para `seller.auditor`

## Evidencia visual relevante

- `e2e/artifacts/public_fix_retry_20260319_155543/06_seller_emit_success.png`
- `e2e/artifacts/public_fix_retry_20260319_155543/07_seller_clients_open.png`
- `e2e/artifacts/public_fix_retry_20260319_155543/08_seller_profile_open.png`
- `e2e/artifacts/public_fix_retry_20260319_155543/09_seller_logout_done.png`

## Ajuste aplicado para estabilizar socios

- Se recompiló `@getupsoft/seller-portal`.
- La página `EmitECF` ahora espera la carga real de la cartera asignada antes de renderizar el selector de clientes.

