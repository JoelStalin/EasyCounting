# ISO-Oriented Cleanliness Baseline - 2026-03-18

## Scope and assumption

The repository already references:

- ISO/IEC 27001
- ISO/IEC 25010

Those are explicit in local compliance and architecture documents.

This baseline keeps those explicit references as the normative core and adds:

- ISO/IEC 12207 as a lifecycle discipline reference
- ISO/IEC 29119 as a testing-discipline reference

Important: this is a **cleanliness and engineering alignment baseline**, not a claim that the project is formally certified under any ISO standard.

## 1. Control matrix

| Area | Practical ISO-oriented objective | Current repo status | Gap | Required action |
| --- | --- | --- | --- | --- |
| Security governance | 27001-aligned secret handling, access control, incident discipline | Partial | Secrets still too dependent on manual operator handling | Move all live secrets to managed secret storage and rotation policy |
| Software quality | 25010 security, reliability, maintainability, compatibility | Partial | Good modularity exists, but runtime validation is incomplete | Add CI gates and runtime verification against real dependencies |
| Lifecycle control | 12207-style traceability and change control | Partial | Many changes are documented, but not all as stable ADR/runbook artifacts | Continue converting chat outcomes into repo-owned docs and decision records |
| Testing discipline | 29119-style evidence, repeatability, coverage, traceability | Partial-to-good | Selenium and pytest evidence exist, but end-to-end certification evidence is incomplete | Add test matrices linking requirements -> cases -> evidence |
| Supplier/security review | 27001 vendor-risk handling | Partial | External services are identified, but only some have explicit risk notes | Maintain per-service review and approval path before prod use |
| Privacy and segregation | 27001 + local law + tenant isolation | Good in chatbot path | Needs broader cross-feature verification | Add tenant-isolation regression suite across all sensitive endpoints |

## 2. Clean state already visible in the project

### 2.1 Good signals

- Multi-tenant separation is explicit in the portal and chatbot layers.
- Rate limiting, readiness, metrics, and optional Sentry are already wired.
- Odoo external-service dependency was reduced by adding internal fallback behavior.
- AI context artifacts now preserve operational knowledge locally.
- Selenium evidence exists, not just unit tests.

### 2.2 Weak signals

- Real DGII certification evidence is still missing.
- Frontend source of truth is not yet fully clean because editable `.ts/.tsx` and emitted `.js` coexist in source trees.
- Some architecture docs are ahead of the runtime implementation.
- Odoo 19 migration was validated statically, not by live instance boot and transactional tests.
- AWS operations exist as scripts but are not yet governed by a full least-privilege CI execution model.

## 3. Clean project baseline by standard

### 3.1 ISO/IEC 27001-oriented baseline

- No plaintext secrets in repo docs or code.
- Managed secret storage for:
  - DGII certificate path and password
  - JWT/HMAC secrets
  - AWS credentials or assumed-role configuration
  - Sentry DSN
  - optional external LLM API keys
- MFA for human administrative access.
- Least-privilege IAM for DNS and infrastructure changes.
- Structured logging with sensitive-field redaction.
- Documented incident response for DGII outage, certificate expiry, and cross-tenant risk.

### 3.2 ISO/IEC 25010-oriented baseline

- Security:
  - tenant isolation test coverage
  - auth/permission regression checks
- Reliability:
  - DGII retry/circuit-breaker tests
  - status-service-aware degradation behavior
- Maintainability:
  - single source of truth for frontend code
  - remove or clearly separate generated artifacts
- Compatibility:
  - live Odoo 19 verification
  - environment parity for frontend builds

### 3.3 ISO/IEC 12207-oriented baseline

- Requirement -> design -> implementation -> test traceability for:
  - DGII emission
  - DGII certification
  - Odoo sync
  - tenant chatbot
- Decision records for transport choice, secret management, and provider choices.
- Release checklist with operational sign-off.

### 3.4 ISO/IEC 29119-oriented baseline

- Test inventory per feature.
- Repeatable test environments.
- Stored evidence for:
  - unit/service tests
  - Selenium visual tests
  - DGII certification test sets
  - Odoo integration tests
- Defect logging tied back to failed evidence.

## 4. Cleanliness backlog

### P0 - must close before claiming a production-clean platform

1. Remove plaintext secret handling from operational workflows.
2. Complete DGII `CERT` evidence with valid certificate-based authentication.
3. Add explicit DGII status-service integration and contingency behavior.
4. Validate tenant isolation beyond chatbot endpoints.

### P1 - should close before a formal go-live

1. Rebuild frontend bundles from source in a reproducible Node toolchain.
2. Decide and implement the real Odoo bridge transport for Odoo 19.
3. Add CI checks for:
   - tests
   - lint/type checks
   - security scanning
   - secret scanning
4. Create environment-specific operational runbooks.

### P2 - quality hardening

1. SBOM generation and dependency inventory.
2. Artifact signing and provenance.
3. Formal policy for Sentry/LLM external data handling.
4. Periodic parser checks for DGII RNC public-page changes.

## 5. Definition of clean for this repo

The project can be described as "clean enough for controlled production rollout" only when all of the following are true:

- no operational secrets are shared through chat or stored in repo docs
- DGII `CERT` flow is executed end to end with preserved evidence
- frontend build is reproducible from source
- Odoo integration path is validated against a real Odoo 19 runtime
- test evidence covers tenant isolation, DGII critical flows, and UI smoke paths
- AWS automation runs with temporary or role-based credentials and least privilege
- documentation reflects the implemented runtime, not only the target architecture

## 6. Local repo references that already support this baseline

- `docs/compliance/SEGURIDAD.md`
- `docs/SEGURIDAD-PROVEEDOR.md`
- `docs/guide/15-implementacion-aws.md`
- `docs/guide/16-arquitectura-eks.md`
- `.ai_context/test_evidence/2026-03-18_selenium_live_demo.md`
- `.ai_context/test_evidence/2026-03-18_wsl_local_service_validation.md`
- `.ai_context/known_issues/2026-03-18_wsl_docker_instability.md`
- `.ai_context/changes_success/2026-03-18_tenant_chatbot_llm.md`
- `.ai_context/changes_success/2026-03-18_dgii_web_rnc_autocomplete.md`
