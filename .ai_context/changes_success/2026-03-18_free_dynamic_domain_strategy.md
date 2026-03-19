# Free Dynamic Domain Strategy - 2026-03-18

## Objective

Prepare a no-AWS publication path for `getupsoft.com.do` that remains compatible with a future AWS migration.

## Chosen direction

Primary recommendation:

- `MiDominio.do` registrar
- `Cloudflare Free` for DNS
- `Cloudflare Tunnel` for public exposure

Fallback recommendation:

- `MiDominio.do` DNS
- stable CNAMEs to a DDNS target
- local update with `ddclient`

## Files added

- `scripts/automation/serve_spa.py`
- `scripts/automation/start_local_public_edge.ps1`
- `scripts/automation/start_cloudflared_quick_tunnel.ps1`
- `ops/cloudflared/getupsoft.com.do.example.yml`
- `ops/ddns/ddclient.duckdns.example.conf`
- `docs/guide/17-dominio-dinamico-gratis-sin-aws.md`
- `docs/guide/18-readiness-futura-aws-desde-dominio-gratis.md`

## Notes

- No live registrar/DNS changes were applied in this step.
- No third-party login was executed in this step.
- A live stable custom-domain cutover still requires Cloudflare account access or API token.
