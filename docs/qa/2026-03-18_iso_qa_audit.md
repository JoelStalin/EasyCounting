# ISO-Oriented QA Audit - 2026-03-18

## Scope

This audit baseline consolidates executable evidence plus a large generated use-case catalog for `dgii_encf`.

Normative framing used in this repo:

- ISO/IEC 25010 (quality characteristics)
- ISO/IEC 29119 (test case specification discipline)
- ISO/IEC 12207 (lifecycle traceability discipline)
- OWASP ASVS (security verification normalization)

## Executed automated evidence

- `pytest`: 53 passed in 37.34s

## Generated use-case catalog

- total cases: `20592`
- CSV: `docs\qa\2026-03-18_use_case_catalog.csv`
- JSONL: `docs\qa\2026-03-18_use_case_catalog.jsonl`
- summary JSON: `docs\qa\2026-03-18_use_case_summary.json`

### Primary streams

- `functional`: 9648
- `regression`: 7488
- `unit`: 3456

### Functional areas covered

- `admin`: 5544
- `auth`: 1320
- `billing`: 528
- `client`: 2904
- `dgii`: 2640
- `frontend_admin`: 792
- `frontend_client`: 1056
- `infra`: 528
- `odoo`: 1320
- `odoo_reports`: 1584
- `recepcion`: 792
- `security`: 1320
- `storage`: 264

### Scenario classes

- `boundary_max`: 1872
- `boundary_min`: 1872
- `cross_tenant`: 1872
- `duplicate_request`: 1872
- `external_timeout`: 1872
- `happy_path`: 1872
- `invalid_format`: 1872
- `missing_required`: 1872
- `regression_route_guard`: 1872
- `security_abuse`: 1872
- `unauthorized`: 1872

### Source families used to normalize use cases

- `dgii_ecf_docs`: 3432
- `dgii_formats`: 2112
- `local_repo`: 13464
- `odoo_portal_docs`: 528
- `owasp_asvs`: 1056

## External/public source families

- `local_repo`: Repository routes, tests, components, addons and notes
- `dgii_ecf_docs`: https://dgii.gov.do/cicloContribuyente/facturacion/comprobantesFiscalesElectronicosE-CF/Paginas/documentacionSobreE-CF.aspx
- `dgii_ecf_types`: https://dgii.gov.do/cicloContribuyente/facturacion/comprobantesFiscalesElectronicosE-CF/Paginas/TipoyEstructurae-CF.aspx
- `dgii_formats`: https://dgii.gov.do/cicloContribuyente/obligacionesTributarias/remisionInformacion/Paginas/formatoEnvioDatos.aspx
- `odoo_portal_docs`: https://www.odoo.com/documentation/19.0/applications/general/users/user_portals.html
- `odoo_portal_access`: https://www.odoo.com/documentation/19.0/applications/general/users/user_portals/portal_access.html
- `owasp_asvs`: https://owasp.org/www-project-application-security-verification-standard/
- `iso_repo_baseline`: docs/compliance/2026-03-18_iso_cleanliness_baseline.md

## Notes

- The catalog is intentionally generated so it can be refreshed after architecture changes.
- Not every generated case is expected to be automated immediately; the catalog is larger than the current executable suite on purpose.
- The catalog mixes positive, boundary, security, tenant-isolation, external-dependency, and regression scenarios.