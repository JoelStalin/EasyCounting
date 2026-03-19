# 2026-03-18 - DNS cutover blocked by missing Cloudflare credentials

## Observed state

- The user provided a registrar screenshot for `getupsoft.com.do`.
- The screenshot shows the domain is still delegated to AWS Route53 nameservers:
  - `ns-1304.awsdns-35.org`
  - `ns-1941.awsdns-50.co.uk`
  - `ns-432.awsdns-54.com`
  - `ns-758.awsdns-30.net`
- No `CLOUDFLARE_API_TOKEN` or `CLOUDFLARE_ACCOUNT_ID` is present on this workstation.
- No prior local Cloudflare configuration was found in `%USERPROFILE%\.cloudflared`.

## Consequence

The domain cannot be cut over to the Cloudflare Free + Tunnel topology until one of these happens:

1. a valid Cloudflare API token is provided and the automation creates/reads the zone, obtains the Cloudflare nameservers, and configures DNS/tunnel/redirects; or
2. the zone is created manually in Cloudflare and the user provides the assigned Cloudflare nameservers so the registrar delegation can be changed.

## Ready automation

The repository is prepared for the live cutover with:

- `scripts/automation/configure_cloudflare_public_edge.ps1`
- `ops/cloudflared/getupsoft.com.do.example.yml`
- `scripts/automation/start_local_public_edge.ps1`

## Pending external inputs

- `CLOUDFLARE_API_TOKEN`
- `CLOUDFLARE_ACCOUNT_ID` when needed for zone creation
