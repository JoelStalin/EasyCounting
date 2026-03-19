# ISO-Audited Test Campaign - 2026-03-18

## Objective

Produce a repeatable QA audit package for `dgii_encf` with:

- executed automated tests
- ISO-oriented normalization criteria
- a large use-case catalog for planning and traceability
- preserved project context

## Executed evidence

Command:

```powershell
.\.venv\Scripts\python -m pytest tests e2e/tests app/tests/unit app/tests/e2e -q
```

Result:

- `53 passed in 37.34s`

Important adjustment made before the final run:

- `tests/test_admin_accounting.py` was refactored to use isolated in-memory SQLite instead of depending on the external `db` hostname.
- This removed environment coupling and made the audit repeatable on the current workstation.

## Generated catalog

Command:

```powershell
.\.venv\Scripts\python scripts/automation/generate_use_case_catalog.py --pytest-summary "53 passed in 37.34s"
```

Result:

- total cases generated: `20592`

Artifacts:

- `docs/qa/2026-03-18_use_case_catalog.csv`
- `docs/qa/2026-03-18_use_case_catalog.jsonl`
- `docs/qa/2026-03-18_use_case_summary.json`
- `docs/qa/2026-03-18_iso_qa_audit.md`
- `docs/qa/2026-03-18_test_traceability_matrix.md`

## Normative baseline used

- ISO/IEC 25010
- ISO/IEC 29119
- ISO/IEC 12207
- ISO/IEC 27001
- OWASP ASVS

This is an engineering-alignment audit package, not a claim of formal external certification.

## Source families used for normalization

- local repository routes, tests, services, addons, and prior AI context
- DGII official e-CF documentation
- DGII official data-format pages
- Odoo official portal documentation
- OWASP ASVS official project guidance

## Remaining gaps

- no live DGII `CERT` end-to-end evidence in this campaign
- no live Odoo 19 runtime boot validation in this campaign
- no formal external auditor sign-off
- no claim of exhaustive web-wide enumeration; the catalog is broad and normalized from official/public families plus repository behavior

## Context preservation

This turn expanded the persistent project memory with:

- `docs/qa/2026-03-18_use_case_catalog.csv`
- `docs/qa/2026-03-18_use_case_catalog.jsonl`
- `docs/qa/2026-03-18_use_case_summary.json`
- `docs/qa/2026-03-18_iso_qa_audit.md`
- `docs/qa/2026-03-18_test_traceability_matrix.md`
- `.ai_context/test_evidence/2026-03-18_iso_audited_test_campaign.md`
