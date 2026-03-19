# 18 - Readiness futura a AWS desde un dominio gratis

## Objective

Keep the project deployable on a free stable edge now, without blocking a later migration to AWS.

## Strategy

The hostname contract must remain stable while the origin changes over time.

Stable public contract:

- `api.getupsoft.com.do`
- `admin.getupsoft.com.do`
- `cliente.getupsoft.com.do`

Current free edge:

- Cloudflare DNS + Cloudflare Tunnel

Future AWS target:

- `api.getupsoft.com.do` -> ALB / API Gateway / ECS / EKS ingress
- `admin.getupsoft.com.do` -> CloudFront + S3 or ALB
- `cliente.getupsoft.com.do` -> CloudFront + S3 or ALB

## Why this is AWS-ready

Because the application and documentation are being aligned around hostnames, not around a fixed provider.

That means the future migration can be:

1. keep Cloudflare as DNS/proxy and only swap origin targets to AWS
2. or move DNS later back to Route53 while preserving the same public FQDNs

## Repository readiness points

- `.env.example` already defaults to:
  - `CLIENT_PORTAL_DOMAIN=cliente.getupsoft.com.do`
  - `ADMIN_PORTAL_DOMAIN=admin.getupsoft.com.do`
- AWS deployment guides already exist:
  - `docs/guide/15-implementacion-aws.md`
  - `docs/guide/16-arquitectura-eks.md`
- Route53 automation scripts remain reusable later:
  - `scripts/automation/configure_aws_route53_profile.ps1`
  - `scripts/automation/update_route53_getupsoft.ps1`

## Migration path later

### Option A - Keep Cloudflare in front

Recommended if you want:

- easier edge security
- caching
- DDoS shielding
- simpler future rollback

In that model, AWS becomes only the origin.

### Option B - Return DNS to Route53

Recommended if you want:

- all infrastructure governance under AWS
- centralized IAM around DNS and infra changes

In that model, the same subdomains are recreated in Route53 and pointed to AWS resources.

## Minimum future AWS resources

- ACM certificates
- ALB or CloudFront
- ECS/EKS workloads
- Secrets Manager / KMS
- RDS / Redis
- Route53 only if you choose full AWS DNS later

## Design rule

Do not hardcode AWS-specific hostnames into application behavior.

Always use:

- environment variables
- reverse proxy headers
- stable public subdomains

This keeps the platform portable across:

- local edge
- Cloudflare edge
- AWS edge
