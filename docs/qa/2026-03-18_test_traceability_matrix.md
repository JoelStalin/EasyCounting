# Test Traceability Matrix - 2026-03-18

## Scope

This matrix links the executed automated suite and the generated use-case catalog to the ISO-oriented baseline already defined in the repository.

Executed command:

```powershell
.\.venv\Scripts\python -m pytest tests e2e/tests app/tests/unit app/tests/e2e -q
```

Result:

- `53 passed in 37.34s`

## Normative framing

| Standard or reference | Practical use in this audit |
| --- | --- |
| ISO/IEC 25010 | Product quality framing: security, reliability, maintainability, compatibility, functional suitability |
| ISO/IEC 29119 | Test-case structure, traceability, repeatability, evidence discipline |
| ISO/IEC 12207 | Lifecycle traceability between requirements, code, tests, and operational notes |
| ISO/IEC 27001 | Access control, secret handling, least privilege, auditability |
| OWASP ASVS | Web/API security checks, abuse cases, authorization verification |

## Executed suites mapped to quality objectives

| Stream | Test files | Main areas | Quality objective |
| --- | --- | --- | --- |
| Unit | `app/tests/unit/test_security.py` | token handling, auth primitives | security, correctness |
| Unit | `app/tests/unit/test_ecf_builder.py` | XML/e-CF generation | functional suitability, maintainability |
| Unit | `app/tests/unit/test_sign_service.py` | signature service | security, reliability |
| Service/API | `app/tests/e2e/test_endpoints.py` | endpoint contract smoke | compatibility, reliability |
| Functional | `tests/test_smoke.py` | application smoke paths | availability, regression control |
| Functional | `tests/test_validation.py` | request validation | functional suitability |
| Functional | `tests/test_xsd_validation.py` | XML schema validation | correctness, compliance support |
| Functional | `tests/test_signing.py` | signing workflow | security, correctness |
| Functional | `tests/test_receptor.py` | receptor flows | reliability, functional suitability |
| Functional | `tests/test_odoo_local_directory.py` | internal RNC directory | autonomy from third parties, reliability |
| Functional | `tests/test_http_ssrf.py` | outbound request hardening | security |
| Functional | `tests/test_file_naming.py` | artifact naming conventions | maintainability, traceability |
| Functional | `tests/test_enfc_endpoints.py` | e-CF endpoints | core business behavior |
| Functional | `tests/test_e2e_local.py` | local integrated behavior | regression, environment sanity |
| Functional | `tests/test_dgii_rnc_web_parser.py` | DGII public lookup parsing | integration reliability |
| Functional | `tests/test_client_chat.py` | tenant-scoped chatbot | tenant isolation, privacy |
| Functional | `tests/test_clients_contract.py` | portal contracts | compatibility |
| Functional | `tests/test_client.py` | client portal flows | functional suitability |
| Functional | `tests/test_admin_accounting.py` | admin accounting flows | correctness, isolation, regression |
| UI / Regression | `e2e/tests/test_admin_smoke.py` | admin portal smoke | usability, route integrity |
| UI / Regression | `e2e/tests/test_client_smoke.py` | client portal smoke | usability, route integrity |

## Coverage focus by area

| Area | Automated evidence | Residual gap |
| --- | --- | --- |
| Authentication and authorization | unit tests + smoke + SSRF/security checks | broader role matrix still needed for all admin endpoints |
| Tenant isolation | chatbot tests and portal flows | full cross-tenant regression matrix is still pending |
| DGII e-CF | endpoint, validation, signing, parser tests | live `CERT` execution evidence still missing |
| Odoo integration | local directory and addon-related tests | live Odoo 19 runtime verification still missing |
| Admin accounting | summary, ledger, settings roundtrip | larger scenario depth still depends on real accounting fixtures |
| Client portal | smoke + contract tests + chatbot tests | bundle rebuild parity and richer UX assertions still pending |
| Frontend | Selenium smoke evidence | source-to-dist reproducibility still pending |
| Security hardening | SSRF, token/security, tenant-scope tests | secret-management and least-privilege runtime controls remain operational tasks |

## Generated use-case catalog linkage

Generated with:

```powershell
.\.venv\Scripts\python scripts/automation/generate_use_case_catalog.py --pytest-summary "53 passed in 37.34s"
```

Outputs:

- `docs/qa/2026-03-18_use_case_catalog.csv`
- `docs/qa/2026-03-18_use_case_catalog.jsonl`
- `docs/qa/2026-03-18_use_case_summary.json`
- `docs/qa/2026-03-18_iso_qa_audit.md`

Summary:

- total cases: `20592`
- functional: `9648`
- regression: `7488`
- unit: `3456`

## Audit conclusion

The repository now has:

- executable evidence for unit, service, regression, and functional checks
- a normalized use-case inventory above the requested 10,000 threshold
- traceability from repo features to test evidence and normative framing

The project does **not** yet have formal certification evidence under any ISO standard, and it does **not** yet have live DGII `CERT` execution evidence in this audit package.
