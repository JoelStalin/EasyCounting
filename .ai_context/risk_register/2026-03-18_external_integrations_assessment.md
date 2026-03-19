# External Integrations Assessment - 2026-03-18

## Objective

This document inventories the external services that materially affect `dgii_encf`, states the current integration level, and records the minimum actions required to make each integration complete and supportable.

This is an engineering assessment, not a certification statement.

## Integration inventory

| Service | Purpose in this project | Current touchpoints | Current status | Main gaps |
| --- | --- | --- | --- | --- |
| DGII e-CF documentation hub | Normative source for XML formats, XSDs, certification process, contingency docs | `docs/oficial/`, `app/infra/settings.py`, multiple DGII flows | Active reference | Must keep local copies synchronized with official updates |
| DGII auth/reception/result APIs | Real e-CF submission lifecycle | `app/dgii/client.py`, `app/application/ecf_submission.py` | Code-ready, not fully certified | Needs real `.p12`, password, DGII certification execution, runtime evidence |
| DGII public RNC/Cedula page | Official partner enrichment/autocomplete source | Odoo localization service/controller | Active and tested | Web scraping fragility; needs monitoring and fallback |
| DGII service status API | Detect outages and maintenance windows | Not yet integrated in runtime logic | Planned only | Needs API key, client wrapper, alerting policy |
| DGII OFV / certification portal | Human workflow for emitter certification and OFV tasks | Operational dependency only | Not automated in repo | Human portal access is not enough; formal certification still depends on digital certificate and test sets |
| Odoo 19 server APIs | Accounting/ERP sync target | Imported addon tree, future bridge service | Partial | Missing runtime bridge, transport choice, Odoo 19 live validation |
| AWS Route53 / IAM / CLI | DNS and public routing automation | `scripts/automation/*.ps1`, `scripts/route53_update.sh` | Scripted, not operationalized in CI | Must use temporary IAM creds, hosted zone scoping, audit trail |
| Sentry | Optional application error tracing | `app/main.py`, `app/infra/settings.py` | Optional hook present | Needs PII policy, environment split, DSN management |
| OpenAI-compatible LLM provider | Optional tenant chatbot generation backend | `app/application/tenant_chat.py` | Optional and abstract | Provider not fixed; must add vendor-specific security review before enabling in prod |

## DGII assessment

### What the official documentation confirms

As of 2026-03-18, the official DGII documentation hub still publishes:

- technical e-CF documentation
- XML format documents
- XSD artifacts
- certification process documents
- contingency instructions

The public page also shows updates in late 2025 and early 2026 for:

- certification process materials
- XML format documents
- XSDs
- contingency guidance

That means this integration is highly time-sensitive and should never rely only on stale memory.

### Technical consequences for this project

1. `app/infra/settings.py` correctly externalizes environment-specific DGII base URLs.
2. `app/dgii/client.py` matches the expected DGII flow shape:
   - get seed
   - sign seed with digital certificate
   - exchange signed seed for token
   - send signed XML payload
   - poll status/result
3. Real certification is still incomplete because OFV credentials alone do not satisfy the machine-authenticated DGII flow.

### Complete-integration checklist for DGII

- Provide valid DGII emitter certificate (`.p12`) for the emitting taxpayer.
- Store certificate and password in managed secret storage, not plain `.env`.
- Execute DGII `CERT` test sets with evidence capture.
- Add runtime client for DGII status-service API.
- Version local XSD and XML references against the official publication dates.
- Record contingency behavior for offline/delayed submission according to DGII guidance.

## DGII RNC public page assessment

### Why it is useful

The official `Consulta RNC` page is a valid authoritative source for partner enrichment and lookup by RNC/Cedula.

### Why it is risky

- It is a human-oriented web page, not a stable public JSON API.
- HTML structure or viewstate fields can change without versioned API guarantees.
- Heavy automation could be rate-limited or broken by anti-automation changes.

### Current mitigation already implemented

- Official lookup is attempted first.
- Internal backend directory fallback exists.
- Local Odoo partner fallback exists.

### Additional actions recommended

- Add synthetic monitoring for parser breakage.
- Add caching with TTL to reduce repeated queries.
- Add circuit breaker behavior in Odoo-side lookup to avoid UI slowdown during DGII page changes.

## DGII status-service API assessment

### Why it matters

The official DGII technical description exposes a service-status API and maintenance-window endpoints. This is exactly the missing operational integration needed for clean contingency handling.

### Current gap

The repo documents DGII contingency, but the running backend does not yet consult the status-service endpoint before or during emissions.

### Required next step

Implement a lightweight `dgii_status_client` that:

- checks service availability
- caches status briefly
- surfaces degraded state in readiness/metrics
- feeds alerting and contingency runbooks

## Odoo 19 assessment

### Current status

- Localization assets were imported and refactored.
- Odoo 19 static compatibility work was done.
- The addon layer already supports DGII-backed partner enrichment.

### Important official constraint

Odoo 19 documents that classic XML-RPC and JSON-RPC endpoints are scheduled for removal in Odoo 20. Building a brand new bridge around deprecated transport would create short-lived integration debt.

### Recommendation

For the missing `odoo_integration` service:

- treat the current addon tree as the domain layer
- design the service around the Odoo 19 replacement path instead of assuming old RPC forever
- keep idempotency, tenant mapping, and accounting sync explicit

## AWS Route53 and IAM assessment

### Good current direction

- The repo already contains Route53 update scripts.
- PowerShell profile configuration now supports session tokens.
- Local documentation already warns against root-account usage.

### Official AWS-aligned posture required

- human users should prefer federation and temporary credentials
- workloads should use temporary credentials when possible
- root credentials should be protected and not used for normal automation
- least privilege must be applied to Route53 actions

### Concrete actions required

- use a dedicated IAM role or limited IAM user for DNS automation
- restrict policy to the exact hosted zone for `getupsoft.com`
- persist CloudTrail evidence for changes
- make CI use OIDC/role assumption rather than long-lived static access keys when possible

## Sentry assessment

### Current status

- `sentry_sdk.init(...)` is already wired behind config.
- `environment` and `traces_sample_rate` are configurable.

### What is missing for clean production use

- a written data-classification policy for what can be sent
- explicit redaction rules for DGII tokens, certificates, RNC/Cedula, and invoice identifiers where required
- different DSNs or projects per environment

## External LLM assessment

### Current status

- The chatbot can run fully local with no external provider.
- External provider mode is abstracted as `openai_compatible`.

### Risk

Without a selected provider, there is no provider-specific DPA, retention model, region policy, or prompt-logging assessment.

### Recommendation

Keep `LLM_PROVIDER=local` as default until:

- provider is selected
- data handling is reviewed
- prompt/response logging policy is defined
- tenant-data minimization is verified against that vendor

## Priority order to complete integrations

1. DGII runtime certification with real certificate and evidence.
2. DGII status-service integration for contingency-aware operation.
3. Odoo runtime bridge for accounting sync.
4. AWS IAM hardening and auditable DNS automation.
5. Optional Sentry production policy.
6. Optional external LLM provider review.

## Official sources consulted on 2026-03-18

- DGII e-CF documentation hub:
  - `https://dgii.gov.do/cicloContribuyente/facturacion/comprobantesFiscalesElectronicosE-CF/Paginas/documentacionSobreE-CF.aspx`
- DGII public RNC consultation:
  - `https://dgii.gov.do/app/WebApps/ConsultasWeb2/ConsultasWeb/consultas/rnc.aspx`
- DGII guide for becoming an electronic issuer:
  - `https://dgii.gov.do/publicacionesOficiales/bibliotecaVirtual/contribuyentes/facturacion/Documents/Facturacion%20Electronica/Guia-Basica-para-ser-Emisor-Electronico.pdf`
- DGII technical description PDF:
  - `https://dgii.gov.do/cicloContribuyente/facturacion/comprobantesFiscalesElectronicosE-CF/Documentacin%20sobre%20eCF/Informe%20y%20Descripci%C3%B3n%20T%C3%A9cnica/Descripcion-tecnica-de-facturacion-electronica.pdf`
- AWS IAM best practices:
  - `https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html`
- AWS temporary credentials:
  - `https://docs.aws.amazon.com/IAM/latest/UserGuide/id_credentials_temp.html`
- AWS CLI config files:
  - `https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-files.html`
- AWS Route53 record set changes:
  - `https://docs.aws.amazon.com/Route53/latest/APIReference/API_ChangeResourceRecordSets.html`
- AWS Route53 record set listing:
  - `https://docs.aws.amazon.com/Route53/latest/APIReference/API_ListResourceRecordSets.html`
- Odoo 19 external RPC API:
  - `https://www.odoo.com/documentation/19.0/developer/reference/external_rpc_api.html`
- Odoo 19 module manifests:
  - `https://www.odoo.com/documentation/19.0/developer/reference/backend/module.html`
- Sentry Python options:
  - `https://docs.sentry.io/platforms/python/configuration/options/`
