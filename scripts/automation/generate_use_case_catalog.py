from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


ROLES = [
    "anonymous",
    "platform_admin",
    "platform_auditor",
    "tenant_user",
    "tenant_billing",
    "portal_user",
    "odoo_operator",
    "internal_service",
]

ENVIRONMENTS = [
    "development",
    "PRECERT",
    "CERT_PROD_LIKE",
]

SCENARIOS = [
    "happy_path",
    "missing_required",
    "invalid_format",
    "boundary_min",
    "boundary_max",
    "unauthorized",
    "cross_tenant",
    "duplicate_request",
    "external_timeout",
    "regression_route_guard",
    "security_abuse",
]

SOURCE_URLS = {
    "local_repo": "Repository routes, tests, components, addons and notes",
    "dgii_ecf_docs": "https://dgii.gov.do/cicloContribuyente/facturacion/comprobantesFiscalesElectronicosE-CF/Paginas/documentacionSobreE-CF.aspx",
    "dgii_ecf_types": "https://dgii.gov.do/cicloContribuyente/facturacion/comprobantesFiscalesElectronicosE-CF/Paginas/TipoyEstructurae-CF.aspx",
    "dgii_formats": "https://dgii.gov.do/cicloContribuyente/obligacionesTributarias/remisionInformacion/Paginas/formatoEnvioDatos.aspx",
    "odoo_portal_docs": "https://www.odoo.com/documentation/19.0/applications/general/users/user_portals.html",
    "odoo_portal_access": "https://www.odoo.com/documentation/19.0/applications/general/users/user_portals/portal_access.html",
    "owasp_asvs": "https://owasp.org/www-project-application-security-verification-standard/",
    "iso_repo_baseline": "docs/compliance/2026-03-18_iso_cleanliness_baseline.md",
}


@dataclass(frozen=True)
class Component:
    component_id: str
    area: str
    kind: str
    local_ref: str
    source_family: str
    allowed_roles: tuple[str, ...]
    priority: str
    multitenant: bool = False
    external_dependency: bool = False
    mutable: bool = False


def _components() -> list[Component]:
    result: list[Component] = []

    def add(
        component_id: str,
        area: str,
        kind: str,
        local_ref: str,
        source_family: str,
        allowed_roles: tuple[str, ...],
        priority: str,
        *,
        multitenant: bool = False,
        external_dependency: bool = False,
        mutable: bool = False,
    ) -> None:
        result.append(
            Component(
                component_id=component_id,
                area=area,
                kind=kind,
                local_ref=local_ref,
                source_family=source_family,
                allowed_roles=allowed_roles,
                priority=priority,
                multitenant=multitenant,
                external_dependency=external_dependency,
                mutable=mutable,
            )
        )

    # Auth
    add("AUTH_LOGIN", "auth", "router", "app/api/routes/auth.py", "local_repo", ("anonymous",), "critical", mutable=True)
    add("AUTH_MFA_VERIFY", "auth", "router", "app/api/routes/auth.py", "local_repo", ("anonymous",), "high", mutable=True)
    add("AUTH_ME", "auth", "router", "app/api/routes/auth.py", "local_repo", ("platform_admin", "platform_auditor", "tenant_user", "tenant_billing"), "high")
    add("AUTH_BOOTSTRAP_ADMIN", "auth", "service", "app/api/routes/auth.py", "local_repo", ("anonymous",), "high", mutable=True)
    add("AUTH_PERMISSION_MAPPING", "auth", "service", "app/api/routes/auth.py", "local_repo", ("internal_service",), "high")

    # Admin portal / admin API
    admin_roles = ("platform_admin", "platform_auditor")
    add("ADMIN_TENANT_LIST", "admin", "router", "app/routers/admin.py", "local_repo", admin_roles, "high")
    add("ADMIN_TENANT_CREATE", "admin", "router", "app/routers/admin.py", "local_repo", admin_roles, "critical", mutable=True)
    add("ADMIN_TENANT_UPDATE", "admin", "router", "app/routers/admin.py", "local_repo", admin_roles, "high", mutable=True)
    add("ADMIN_TENANT_GET", "admin", "router", "app/routers/admin.py", "local_repo", admin_roles, "medium")
    add("ADMIN_DASHBOARD_KPI", "admin", "router", "app/routers/admin.py", "local_repo", admin_roles, "medium")
    add("ADMIN_INVOICE_LIST", "admin", "router", "app/routers/admin.py", "local_repo", admin_roles, "high", multitenant=True)
    add("ADMIN_INVOICE_DETAIL", "admin", "router", "app/routers/admin.py", "local_repo", admin_roles, "high", multitenant=True)
    add("ADMIN_PLAN_LIST", "admin", "router", "app/routers/admin.py", "local_repo", admin_roles, "medium")
    add("ADMIN_PLAN_CREATE", "admin", "router", "app/routers/admin.py", "local_repo", admin_roles, "high", mutable=True)
    add("ADMIN_PLAN_UPDATE", "admin", "router", "app/routers/admin.py", "local_repo", admin_roles, "high", mutable=True)
    add("ADMIN_PLAN_DELETE", "admin", "router", "app/routers/admin.py", "local_repo", admin_roles, "high", mutable=True)
    add("ADMIN_LEDGER_SUMMARY", "admin", "router", "app/routers/admin.py", "local_repo", admin_roles, "high", multitenant=True)
    add("ADMIN_LEDGER_LIST", "admin", "router", "app/routers/admin.py", "local_repo", admin_roles, "high", multitenant=True)
    add("ADMIN_LEDGER_CREATE", "admin", "router", "app/routers/admin.py", "local_repo", admin_roles, "critical", multitenant=True, mutable=True)
    add("ADMIN_TENANT_SETTINGS_GET", "admin", "router", "app/routers/admin.py", "local_repo", admin_roles, "medium", multitenant=True)
    add("ADMIN_TENANT_SETTINGS_UPDATE", "admin", "router", "app/routers/admin.py", "local_repo", admin_roles, "high", multitenant=True, mutable=True)
    add("ADMIN_TENANT_PLAN_ASSIGN", "admin", "router", "app/routers/admin.py", "local_repo", admin_roles, "high", multitenant=True, mutable=True)
    add("ADMIN_TENANT_PLAN_GET", "admin", "router", "app/routers/admin.py", "local_repo", admin_roles, "medium", multitenant=True)
    add("ADMIN_BILLING_SUMMARY", "admin", "router", "app/routers/admin.py", "local_repo", admin_roles, "medium")
    add("ADMIN_AUDIT_LOGS", "admin", "router", "app/routers/admin.py", "local_repo", admin_roles, "high", multitenant=True)
    add("ADMIN_PLATFORM_USERS", "admin", "router", "app/routers/admin.py", "local_repo", admin_roles, "medium")

    # Client portal / tenant API
    tenant_roles = ("tenant_user", "tenant_billing")
    add("CLIENT_HEALTH", "client", "router", "app/routers/cliente.py", "local_repo", tenant_roles, "low")
    add("CLIENT_ME", "client", "router", "app/routers/cliente.py", "local_repo", tenant_roles, "medium", multitenant=True)
    add("CLIENT_PLAN_LIST", "client", "router", "app/routers/cliente.py", "local_repo", tenant_roles, "medium", multitenant=True)
    add("CLIENT_PLAN_GET", "client", "router", "app/routers/cliente.py", "local_repo", tenant_roles, "medium", multitenant=True)
    add("CLIENT_PLAN_CHANGE", "client", "router", "app/routers/cliente.py", "local_repo", tenant_roles, "high", multitenant=True, mutable=True)
    add("CLIENT_USAGE", "client", "router", "app/routers/cliente.py", "local_repo", tenant_roles, "high", multitenant=True)
    add("CLIENT_INVOICE_LIST", "client", "router", "app/routers/cliente.py", "local_repo", tenant_roles, "critical", multitenant=True)
    add("CLIENT_INVOICE_DETAIL", "client", "router", "app/routers/cliente.py", "local_repo", tenant_roles, "critical", multitenant=True)
    add("CLIENT_CHAT_ASK", "client", "router", "app/routers/cliente.py", "local_repo", tenant_roles, "critical", multitenant=True, external_dependency=True, mutable=True)
    add("CLIENT_PORTAL_SERVICE", "client", "service", "app/application/client_portal.py", "local_repo", ("internal_service",), "high", multitenant=True)
    add("TENANT_CHAT_SERVICE", "client", "service", "app/application/tenant_chat.py", "local_repo", ("internal_service",), "critical", multitenant=True, external_dependency=True)

    # Odoo support / local directory
    add("ODOO_RNC_SEARCH", "odoo", "router", "app/routers/odoo.py", "dgii_formats", ("odoo_operator", "internal_service"), "high", external_dependency=False)
    add("ODOO_RNC_LOOKUP", "odoo", "router", "app/routers/odoo.py", "dgii_formats", ("odoo_operator", "internal_service"), "high", external_dependency=False)
    add("LOCAL_RNC_DIRECTORY", "odoo", "service", "app/services/local_rnc_directory.py", "local_repo", ("internal_service",), "high")
    add("ODOO_PARTNER_ENRICHMENT", "odoo", "service", "integration/odoo/getupsoft_do_localization/getupsoft_l10n_do_accounting/models/res_partner.py", "odoo_portal_docs", ("odoo_operator",), "high", external_dependency=True, mutable=True)
    add("ODOO_DGII_AUTOCOMPLETE", "odoo", "router", "integration/odoo/getupsoft_do_localization/getupsoft_l10n_do_rnc_search/controllers/controllers.py", "odoo_portal_docs", ("odoo_operator",), "high", external_dependency=True)

    # DGII / submission
    add("DGII_ECF_SUBMIT", "dgii", "service", "app/application/ecf_submission.py", "dgii_ecf_docs", ("internal_service",), "critical", multitenant=True, external_dependency=True, mutable=True)
    add("DGII_RFCE_SUBMIT", "dgii", "service", "app/dgii/client.py", "dgii_ecf_docs", ("internal_service",), "critical", multitenant=True, external_dependency=True, mutable=True)
    add("DGII_ACECF_SUBMIT", "dgii", "service", "app/dgii/client.py", "dgii_ecf_docs", ("internal_service",), "high", multitenant=True, external_dependency=True, mutable=True)
    add("DGII_ARECF_SUBMIT", "dgii", "service", "app/dgii/client.py", "dgii_ecf_docs", ("internal_service",), "high", multitenant=True, external_dependency=True, mutable=True)
    add("DGII_ANECF_SUBMIT", "dgii", "service", "app/dgii/client.py", "dgii_ecf_docs", ("internal_service",), "high", multitenant=True, external_dependency=True, mutable=True)
    add("DGII_TOKEN_FLOW", "dgii", "service", "app/dgii/client.py", "dgii_ecf_docs", ("internal_service",), "critical", external_dependency=True, mutable=True)
    add("DGII_STATUS_QUERY", "dgii", "service", "app/dgii/client.py", "dgii_ecf_docs", ("internal_service",), "high", multitenant=True, external_dependency=True)
    add("DGII_RESULT_QUERY", "dgii", "service", "app/dgii/client.py", "dgii_ecf_docs", ("internal_service",), "high", multitenant=True, external_dependency=True)
    add("DGII_XSD_VALIDATION", "dgii", "validator", "app/dgii/validation.py", "dgii_ecf_docs", ("internal_service",), "critical")
    add("DGII_XML_SIGNING", "dgii", "security", "app/dgii/signing.py", "dgii_ecf_docs", ("internal_service",), "critical")

    # ENFC / receptor / RI
    add("ENFC_ENDPOINTS", "recepcion", "router", "app/api/enfc_routes.py", "dgii_ecf_docs", ("internal_service",), "high", external_dependency=True, mutable=True)
    add("RECEPTOR_ENDPOINTS", "recepcion", "router", "app/api/routes/receptor.py", "dgii_ecf_docs", ("internal_service",), "high", external_dependency=True, mutable=True)
    add("RI_RENDERING", "recepcion", "router", "app/api/routes/ri.py", "dgii_ecf_docs", ("tenant_user", "tenant_billing", "platform_admin", "internal_service"), "medium", multitenant=True)

    # Security / infra
    add("AUDIT_HASH_CHAIN", "security", "model", "app/models/audit.py", "owasp_asvs", ("internal_service",), "critical", multitenant=True)
    add("HEALTH_PROBES", "infra", "router", "app/main.py", "local_repo", ("anonymous", "internal_service"), "medium")
    add("METRICS_ENDPOINT", "infra", "router", "app/main.py", "local_repo", ("internal_service",), "medium")
    add("RATE_LIMITING", "security", "security", "app/security/rate_limit.py", "owasp_asvs", ("internal_service",), "high")
    add("SECURITY_HEADERS", "security", "security", "app/main.py", "owasp_asvs", ("anonymous", "internal_service"), "high")
    add("SSRF_GUARD", "security", "security", "tests/test_http_ssrf.py", "owasp_asvs", ("internal_service",), "critical")
    add("FILE_NAMING", "security", "validator", "tests/test_file_naming.py", "local_repo", ("internal_service",), "medium")
    add("STORAGE_XML_HASH", "storage", "service", "app/shared/storage.py", "local_repo", ("internal_service",), "high", multitenant=True, mutable=True)

    # Frontend
    add("FRONTEND_ADMIN_ROUTE_GUARDS", "frontend_admin", "ui", "frontend/apps/admin-portal/src/routes.tsx", "local_repo", admin_roles, "high")
    add("FRONTEND_ADMIN_COMPANIES_PAGE", "frontend_admin", "ui", "frontend/apps/admin-portal/src/pages/Companies.tsx", "local_repo", admin_roles, "high", mutable=True)
    add("FRONTEND_ADMIN_AUDIT_PAGE", "frontend_admin", "ui", "frontend/apps/admin-portal/src/pages/AuditLogs.tsx", "local_repo", admin_roles, "medium")
    add("FRONTEND_CLIENT_ROUTE_GUARDS", "frontend_client", "ui", "frontend/apps/client-portal/src/routes.tsx", "local_repo", tenant_roles, "high")
    add("FRONTEND_CLIENT_EMIT_PAGE", "frontend_client", "ui", "frontend/apps/client-portal/src/pages/EmitECF.tsx", "local_repo", tenant_roles, "high", mutable=True)
    add("FRONTEND_CLIENT_PROFILE_PAGE", "frontend_client", "ui", "frontend/apps/client-portal/src/pages/Profile.tsx", "local_repo", tenant_roles, "medium")
    add("FRONTEND_CLIENT_ASSISTANT_PAGE", "frontend_client", "ui", "frontend/apps/client-portal/src/pages/Assistant.tsx", "local_repo", tenant_roles, "high", multitenant=True, external_dependency=True, mutable=True)

    # Odoo reporting / fiscal files
    report_roles = ("odoo_operator", "platform_admin", "internal_service")
    add("ODOO_REPORT_606", "odoo_reports", "report", "integration/odoo/getupsoft_do_localization/getupsoft_l10n_do_accounting_report/models/dgii_report.py", "dgii_formats", report_roles, "critical", mutable=True)
    add("ODOO_REPORT_607", "odoo_reports", "report", "integration/odoo/getupsoft_do_localization/getupsoft_l10n_do_accounting_report/models/dgii_report.py", "dgii_formats", report_roles, "critical", mutable=True)
    add("ODOO_REPORT_608", "odoo_reports", "report", "integration/odoo/getupsoft_do_localization/getupsoft_l10n_do_accounting_report/models/dgii_report.py", "dgii_formats", report_roles, "high", mutable=True)
    add("ODOO_REPORT_609", "odoo_reports", "report", "integration/odoo/getupsoft_do_localization/getupsoft_l10n_do_accounting_report/models/dgii_report.py", "dgii_formats", report_roles, "high", mutable=True)
    add("ODOO_REPORT_IT1", "odoo_reports", "report", "integration/odoo/getupsoft_do_localization/getupsoft_l10n_do_accounting_report/views/dgii_report_view.xml", "dgii_formats", report_roles, "high")
    add("ODOO_REPORT_DOWNLOADS", "odoo_reports", "report", "integration/odoo/getupsoft_do_localization/getupsoft_l10n_do_accounting_report/views/dgii_report_view.xml", "dgii_formats", report_roles, "high")

    # Pricing / billing
    add("PRICING_PLAN_RULES", "billing", "service", "app/models/billing.py", "local_repo", ("internal_service", "platform_admin"), "high")
    add("USAGE_RECORD_BILLING", "billing", "service", "app/application/ecf_submission.py", "local_repo", ("internal_service",), "high", multitenant=True, mutable=True)

    return result


def iso_quality_for(component: Component, scenario: str) -> str:
    values = {"functional_suitability"}
    if component.kind in {"security", "validator"} or scenario in {"unauthorized", "cross_tenant", "security_abuse"}:
        values.add("security")
    if component.external_dependency or scenario == "external_timeout":
        values.add("reliability")
    if component.kind == "ui":
        values.add("usability")
    if component.area.startswith("frontend") or component.area == "odoo":
        values.add("compatibility")
    if component.kind in {"service", "model", "validator"}:
        values.add("maintainability")
    return ",".join(sorted(values))


def primary_stream(component: Component, scenario: str) -> str:
    if scenario in {"unauthorized", "cross_tenant", "security_abuse", "regression_route_guard"}:
        return "regression"
    if component.kind in {"ui", "router", "report"} or scenario == "external_timeout":
        return "functional"
    return "unit"


def expected_result(component: Component, role: str, scenario: str) -> str:
    allowed = role in component.allowed_roles
    if scenario == "happy_path":
        if allowed:
            return "Operation succeeds, contract is respected, and audit/state changes occur when mutable."
        return "Access is denied or redirected without privilege escalation."
    if scenario == "missing_required":
        return "Validation error is returned without corrupting persisted state."
    if scenario == "invalid_format":
        return "Input is rejected with explicit validation feedback and no unsafe fallback."
    if scenario == "boundary_min":
        return "Minimum valid payload or state is processed consistently with documented defaults."
    if scenario == "boundary_max":
        return "Upper-bound payload is handled without truncation, timeout, or silent data loss."
    if scenario == "unauthorized":
        return "Unauthorized access is blocked with 401/403/redirect and no data disclosure."
    if scenario == "cross_tenant":
        if component.multitenant:
            return "Cross-tenant access is denied or sanitized; no foreign tenant data is leaked."
        return "No tenant boundary bypass is possible; unrelated records remain hidden."
    if scenario == "duplicate_request":
        return "Duplicate request is idempotent or rejected deterministically without double effects."
    if scenario == "external_timeout":
        if component.external_dependency:
            return "Timeout triggers retry, fallback, warning, or degraded response without inconsistent state."
        return "Component remains stable even when dependent collaborators are unavailable."
    if scenario == "regression_route_guard":
        return "Previously protected flow remains protected after code or config changes."
    if scenario == "security_abuse":
        return "Abuse is rate-limited, rejected, logged, or neutralized without compromising integrity."
    raise ValueError(f"Unsupported scenario: {scenario}")


def preconditions(component: Component, role: str, environment: str, scenario: str) -> str:
    items = [f"environment={environment}", f"role={role}", f"component={component.component_id}"]
    if component.external_dependency:
        items.append("external_dependency_stub_or_controlled_fixture")
    if component.multitenant:
        items.append("tenant_context_available")
    if scenario in {"duplicate_request", "cross_tenant"}:
        items.append("baseline_record_exists")
    if scenario == "regression_route_guard":
        items.append("previously_verified_baseline_available")
    return ";".join(items)


def source_refs(component: Component) -> str:
    refs = [component.local_ref, SOURCE_URLS[component.source_family], SOURCE_URLS["owasp_asvs"], SOURCE_URLS["iso_repo_baseline"]]
    return " | ".join(refs)


def build_cases() -> list[dict[str, str]]:
    components = _components()
    rows: list[dict[str, str]] = []
    counter = 1

    for component in components:
        for role in ROLES:
            for environment in ENVIRONMENTS:
                for scenario in SCENARIOS:
                    stream = primary_stream(component, scenario)
                    rows.append(
                        {
                            "case_id": f"UC-{counter:05d}",
                            "component_id": component.component_id,
                            "area": component.area,
                            "kind": component.kind,
                            "role": role,
                            "environment": environment,
                            "scenario": scenario,
                            "primary_stream": stream,
                            "priority": component.priority,
                            "multitenant": "yes" if component.multitenant else "no",
                            "external_dependency": "yes" if component.external_dependency else "no",
                            "mutable": "yes" if component.mutable else "no",
                            "allowed_role": "yes" if role in component.allowed_roles else "no",
                            "iso_25010_focus": iso_quality_for(component, scenario),
                            "iso_29119_artifact": "test_case_specification",
                            "security_reference": "OWASP ASVS",
                            "source_family": component.source_family,
                            "local_ref": component.local_ref,
                            "preconditions": preconditions(component, role, environment, scenario),
                            "expected_result": expected_result(component, role, scenario),
                            "description": (
                                f"Validate {component.component_id} for role={role}, env={environment}, "
                                f"scenario={scenario} using auditable expectations."
                            ),
                            "source_refs": source_refs(component),
                        }
                    )
                    counter += 1

    return rows


def write_outputs(rows: list[dict[str, str]], out_dir: Path, pytest_summary: str) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    csv_path = out_dir / "2026-03-18_use_case_catalog.csv"
    jsonl_path = out_dir / "2026-03-18_use_case_catalog.jsonl"
    summary_path = out_dir / "2026-03-18_use_case_summary.json"
    md_path = out_dir / "2026-03-18_iso_qa_audit.md"

    fieldnames = list(rows[0].keys())
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    with jsonl_path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")

    by_stream = Counter(row["primary_stream"] for row in rows)
    by_area = Counter(row["area"] for row in rows)
    by_scenario = Counter(row["scenario"] for row in rows)
    by_role = Counter(row["role"] for row in rows)
    by_source = Counter(row["source_family"] for row in rows)

    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_cases": len(rows),
        "streams": dict(sorted(by_stream.items())),
        "areas": dict(sorted(by_area.items())),
        "scenarios": dict(sorted(by_scenario.items())),
        "roles": dict(sorted(by_role.items())),
        "source_families": dict(sorted(by_source.items())),
        "pytest_summary": pytest_summary,
        "catalog_files": {
            "csv": str(csv_path),
            "jsonl": str(jsonl_path),
        },
        "source_urls": SOURCE_URLS,
    }

    with summary_path.open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2, ensure_ascii=False)

    area_table = "\n".join(f"- `{key}`: {value}" for key, value in sorted(by_area.items()))
    stream_table = "\n".join(f"- `{key}`: {value}" for key, value in sorted(by_stream.items()))
    scenario_table = "\n".join(f"- `{key}`: {value}" for key, value in sorted(by_scenario.items()))
    source_table = "\n".join(f"- `{key}`: {value}" for key, value in sorted(by_source.items()))
    source_urls_md = "\n".join(f"- `{key}`: {value}" for key, value in SOURCE_URLS.items())

    md_path.write_text(
        "\n".join(
            [
                "# ISO-Oriented QA Audit - 2026-03-18",
                "",
                "## Scope",
                "",
                "This audit baseline consolidates executable evidence plus a large generated use-case catalog for `dgii_encf`.",
                "",
                "Normative framing used in this repo:",
                "",
                "- ISO/IEC 25010 (quality characteristics)",
                "- ISO/IEC 29119 (test case specification discipline)",
                "- ISO/IEC 12207 (lifecycle traceability discipline)",
                "- OWASP ASVS (security verification normalization)",
                "",
                "## Executed automated evidence",
                "",
                f"- `pytest`: {pytest_summary}",
                "",
                "## Generated use-case catalog",
                "",
                f"- total cases: `{len(rows)}`",
                f"- CSV: `{csv_path}`",
                f"- JSONL: `{jsonl_path}`",
                f"- summary JSON: `{summary_path}`",
                "",
                "### Primary streams",
                "",
                stream_table,
                "",
                "### Functional areas covered",
                "",
                area_table,
                "",
                "### Scenario classes",
                "",
                scenario_table,
                "",
                "### Source families used to normalize use cases",
                "",
                source_table,
                "",
                "## External/public source families",
                "",
                source_urls_md,
                "",
                "## Notes",
                "",
                "- The catalog is intentionally generated so it can be refreshed after architecture changes.",
                "- Not every generated case is expected to be automated immediately; the catalog is larger than the current executable suite on purpose.",
                "- The catalog mixes positive, boundary, security, tenant-isolation, external-dependency, and regression scenarios.",
            ]
        ),
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate auditable QA use-case catalog for dgii_encf.")
    parser.add_argument(
        "--out-dir",
        default="docs/qa",
        help="Output directory for CSV/JSONL/summary files.",
    )
    parser.add_argument(
        "--pytest-summary",
        default="not provided",
        help="Human-readable pytest summary to embed in the audit output.",
    )
    args = parser.parse_args()

    rows = build_cases()
    write_outputs(rows, Path(args.out_dir), args.pytest_summary)

    print(f"TOTAL_CASES={len(rows)}")
    print(f"OUT_DIR={Path(args.out_dir).resolve()}")


if __name__ == "__main__":
    main()
