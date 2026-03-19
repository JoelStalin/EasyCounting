# 12 — Scripts operativos

Incluye ejemplos de uso para `scripts/setup_env.py`, `scripts/encrypt_env.py` y `scripts/sample_curl.sh`, con consideraciones de seguridad para claves AES-GCM.

## Exposición pública sin AWS

Scripts agregados para exponer el entorno local con una opción gratuita y portable:

- `scripts/automation/serve_spa.py`
- `scripts/automation/start_local_public_edge.ps1`
- `scripts/automation/start_cloudflared_quick_tunnel.ps1`

Archivos de apoyo:

- `ops/cloudflared/getupsoft.com.do.example.yml`
- `ops/ddns/ddclient.duckdns.example.conf`

Guías relacionadas:

- `docs/guide/17-dominio-dinamico-gratis-sin-aws.md`
- `docs/guide/18-readiness-futura-aws-desde-dominio-gratis.md`
