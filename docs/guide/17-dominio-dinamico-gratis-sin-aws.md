# 17 - Dominio dinamico gratis sin AWS

## Decision

For `getupsoft.com.do`, the best free and stable path is:

1. keep the domain registered at `MiDominio.do`
2. move DNS authority to `Cloudflare Free`
3. publish the local project with `Cloudflare Tunnel` using `cloudflared`

This avoids:

- AWS Route53 costs
- dependence on fixed public IP
- inbound port forwarding from the ISP/router
- direct exposure of the home/office IP

## Why this is better than direct DNS at MiDominio

`MiDominio.do` can manage DNS records, but their DNS console documentation indicates a minimum TTL of `14400` seconds for common records. That is a poor fit for dynamic-IP origin changes.

With `Cloudflare Tunnel`:

- the domain remains stable
- the origin IP may change without touching public DNS
- the exposed entrypoint keeps the same public hostnames

## Target hostnames

- `api.getupsoft.com.do`
- `admin.getupsoft.com.do`
- `cliente.getupsoft.com.do`

The repository is already aligned with these hostnames in `.env.example`.

## Local services mapping

Expected local ports:

- API: `http://127.0.0.1:28080`
- Admin SPA: `http://127.0.0.1:18081`
- Client SPA: `http://127.0.0.1:18082`

Relevant files:

- `deploy/docker-compose.wsl-local.yml`
- `ops/nginx.local.conf`
- `scripts/automation/serve_spa.py`
- `scripts/automation/start_local_public_edge.ps1`
- `ops/cloudflared/getupsoft.com.do.example.yml`

## Recommended implementation

### Phase 1 - Local public edge

1. Start the local application stack.
2. Serve `admin-portal/dist` and `client-portal/dist` on local loopback ports.
3. Verify:
   - `http://127.0.0.1:28080/healthz`
   - `http://127.0.0.1:18081/login`
   - `http://127.0.0.1:18082/login`

Command:

```powershell
.\scripts\automation\start_local_public_edge.ps1 -StartDocker
```

### Phase 2 - Cloudflare Free

1. Create or access a Cloudflare account.
2. Add zone `getupsoft.com.do`.
3. Cloudflare will assign authoritative nameservers.
4. In `MiDominio.do`, replace current nameservers with the Cloudflare nameservers.

Important:

- this is a one-time registrar action
- after propagation, DNS records will be managed in Cloudflare, not in AWS

### Phase 3 - Named tunnel

Install `cloudflared`, authenticate, create a tunnel, then use the config template.

Recommended API-token permissions:

- `Account -> Cloudflare Tunnel -> Edit`
- `Zone -> DNS -> Edit`
- `Zone -> Single Redirect -> Edit`
- `Zone -> Zone -> Edit` only if you want the script to create the zone when it does not exist

Automation entrypoint:

```powershell
.\scripts\automation\configure_cloudflare_public_edge.ps1 `
  -ApiToken "<CLOUDFLARE_API_TOKEN>" `
  -AccountId "<CLOUDFLARE_ACCOUNT_ID>" `
  -CreateZoneIfMissing `
  -InstallTunnelService
```

Manual flow:

```powershell
cloudflared login
cloudflared tunnel create getupsoft-local
cloudflared tunnel route dns getupsoft-local api.getupsoft.com.do
cloudflared tunnel route dns getupsoft-local admin.getupsoft.com.do
cloudflared tunnel route dns getupsoft-local cliente.getupsoft.com.do
cloudflared tunnel --config ops/cloudflared/getupsoft.com.do.example.yml run
```

## Fallback if Cloudflare is not available yet

If you need a no-AWS fallback before moving nameservers:

1. create a `DuckDNS` hostname
2. keep DNS in `MiDominio.do`
3. add stable CNAMEs from:
   - `api.getupsoft.com.do`
   - `admin.getupsoft.com.do`
   - `cliente.getupsoft.com.do`
4. update the DuckDNS record from this machine using an open-source client like `ddclient`

Example config template:

- `ops/ddns/ddclient.duckdns.example.conf`

This fallback is cheaper and simple, but still weaker than Cloudflare Tunnel because the origin remains directly reachable and depends on the DDNS service.

## Sources

- MiDominio DNS records guide: `https://cp.midominio.do/kb/servlet/KBServlet/faq471.html`
- MiDominio HTTP API integration guide: `https://cp.midominio.do/kb/answer/954`
- Cloudflare Tunnel docs: `https://developers.cloudflare.com/tunnel/`
- Cloudflare Single Redirects API: `https://developers.cloudflare.com/rules/url-forwarding/single-redirects/create-api/`
- Cloudflare dynamic IP docs: `https://developers.cloudflare.com/dns/manage-dns-records/how-to/managing-dynamic-ip-addresses`
- cloudflared repository: `https://github.com/cloudflare/cloudflared`
