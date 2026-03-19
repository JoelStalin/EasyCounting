# Chefalitas Odoo Audit - 2026-03-18

## Scope

This note captures the initial technical audit of the Odoo environment located at:

- `C:\Users\yoeli\Documents\Chefalitas`

## Environment summary

- Product: Odoo deployment repository
- Odoo version: `18.0`
- Runtime stack in repo:
  - Odoo
  - PostgreSQL 15
  - Nginx
  - Certbot
  - pgAdmin
- Public domain documented in repo:
  - `https://chefalitas.com.do`

## Relevant repo files

- `README.md`
- `docker-compose.yml`
- `config/odoo.conf`
- `addons/l10n_do_accounting`
- `addons/l10n_do_accounting_report`
- `addons/pos_kitchen_core`
- `addons/pos_printing_suite`
- `addons/pos_system`

## Key findings

### 1. The repo already includes Dominican fiscal reporting

`addons/l10n_do_accounting_report` is not a placeholder. It already generates:

- 606
- 607
- 608
- 609
- IT-1 helper summaries
- consumer invoice summaries

Generated outputs are stored as TXT binaries on the Odoo model and exposed in the UI.

### 2. "Publish to DGII" is not implemented

The current report flow supports:

- generation
- attachment/download
- internal state transition to `sent`

It does **not** implement an official DGII API upload for 606/607/608/609. The current `state_sent()` method is an internal bookkeeping action, not proof of OFV submission.

### 3. The environment looks production-oriented

Signals:

- real public domain
- Certbot and Nginx TLS setup
- deployment workflow via GitHub Actions
- prior notes about SSH access and production POS session management

Because of that, destructive or state-changing tests should not run casually against the live site.

### 4. Docker is not currently available on this host

The local stack could not be inspected via `docker ps` because the Docker daemon/pipe is not available in this machine state.

Consequence:

- local runtime validation from this workstation is blocked until Docker is available again
- direct testing would otherwise have to target the public live environment, which is riskier

### 4.1 Public DNS resolution is currently failing from this host

Non-destructive HTTP probes to:

- `https://chefalitas.com.do/`
- `https://chefalitas.com.do/web/login`
- `https://chefalitas.com.do/my`

all failed with:

- `The remote name could not be resolved: 'chefalitas.com.do'`

Consequence:

- external Selenium or browser validation against the public site is blocked from this host right now
- AWS/Route53 or upstream DNS publication must be verified before portal testing

### 5. Existing Selenium artifacts are already present

The repo contains prior Selenium probes under `tmp/`, including POS flows and console captures.

Important existing evidence:

- `tmp/selenium_user_report.json`
- `tmp/selenium_pos_report.json`
- `tmp/probe_debug_legacy_summary.json`
- `tmp/summary_before_publish.json`
- `tmp/summary_after_publish.json`

### 6. A known live POS issue already exists

Prior local memory in `context/LONG_TERM_MEMORY.md` records that POS printing remained blocked by browser loopback/PNA restrictions when attempting to call `http://127.0.0.1:9060` from an HTTPS origin.

That means POS printing validation is not just an application question; browser/network policy is part of the problem.

## DGII-reporting implications for Chefalitas

Based on official DGII materials reviewed on 2026-03-18:

- formats 606/607/608/609 are submitted through Oficina Virtual DGII as TXT files
- DGII provides pre-validation tooling for 606/607/608
- 606 requires prior validation by DGII before related ITBIS credit handling
- if a taxpayer is 100% electronic, 607 and 608 may no longer be required in the same way, depending on the exact operating scenario documented by DGII

For Chefalitas this means the report module should be treated as:

- generation engine: yes
- OFV upload automation: not currently present
- regulatory logic by operating mode: needs explicit review against current DGII status of the company

## What can be done safely right now

- inspect and refactor report generation code
- add export traceability and operational logs
- prepare non-destructive Selenium smoke tests
- document the exact manual/semiautomated OFV submission flow
- prepare AWS and DGII integration runbooks

## What should not be done blindly

- use AWS root console for configuration
- run destructive POS/order tests against production without a safe test user and window
- automate real OFV/DGII submission from a live taxpayer account without explicit operational approval
- assume DGII 607/608 obligations without verifying whether Chefalitas is already operating under 100% e-CF rules

## Prerequisites to continue live execution

1. Confirm whether `chefalitas.com.do` is production only or there is a staging/test DB.
2. Provide dedicated non-production users for:
   - backend admin
   - POS operator
   - customer portal
   - partner/supplier portal if applicable
3. Provide temporary AWS IAM credentials or assumable role, not root credentials.
4. Provide DGII `CERT` certificate path/password if e-CF runtime certification is expected.
5. Confirm whether Chefalitas is:
   - partially electronic
   - fully electronic
   - using only e-CF series E for sales

That last point changes the expected behavior of 607/608 reporting materially.
