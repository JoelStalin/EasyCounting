from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True, slots=True)
class RequiredArtifact:
    category: str
    name: str
    path: str
    kind: str
    required: bool = True
    note: str = ""


REQUIRED_ARTIFACTS: tuple[RequiredArtifact, ...] = (
    RequiredArtifact("business_context", "master_business_audit", "docs/business/2026-03-19_auditoria_repositorio_mercado_pricing.md", "doc"),
    RequiredArtifact("business_context", "market_pricing_note", ".ai_context/notes/2026-03-19_repo_market_pricing_audit.md", "note"),
    RequiredArtifact("business_context", "long_term_prompt_memory", ".ai_context/notes/LONG_TERM_PROMPT_MEMORY.md", "memory"),
    RequiredArtifact("chat_memory", "chat_policy_file", ".ai_context/notes/chat_memory_policy.json", "policy"),
    RequiredArtifact("chat_memory", "prompt_catalog", ".ai_context/notes/prompt_catalog.json", "index"),
    RequiredArtifact("chat_memory", "prompt_dictionary", ".ai_context/notes/prompt_dictionary.json", "index"),
    RequiredArtifact("chat_memory", "save_chat_history_cli", "scripts/automation/save_chat_history.py", "script"),
    RequiredArtifact("chat_memory", "close_chat_session_cli", "scripts/automation/close_project_chat_session.py", "script"),
    RequiredArtifact("chat_memory", "chat_memory_compliance_cli", "scripts/automation/check_chat_memory_compliance.py", "script"),
    RequiredArtifact("chat_memory", "chat_memory_tests", "tests/test_chat_memory.py", "test"),
    RequiredArtifact("plans_and_pricing", "plans_pricing_guide", "docs/guide/13-planes-tarifas.md", "doc"),
    RequiredArtifact("plans_and_pricing", "billing_model", "app/models/billing.py", "code"),
    RequiredArtifact("plans_and_pricing", "recurring_invoices_service", "app/application/recurring_invoices.py", "code"),
    RequiredArtifact("plans_and_pricing", "recurring_invoices_tests", "tests/test_recurring_invoices.py", "test"),
    RequiredArtifact("demo_and_sales", "demo_setup", "scripts/automation/setup_demo_environment.py", "script"),
    RequiredArtifact("demo_and_sales", "demo_seed", "scripts/automation/seed_public_demo_data.py", "script"),
    RequiredArtifact("demo_and_sales", "corporate_portal", "frontend/apps/corporate-portal/index.html", "frontend"),
    RequiredArtifact("demo_and_sales", "seller_portal", "frontend/apps/seller-portal/src/pages/Login.tsx", "frontend"),
    RequiredArtifact("enterprise_and_odoo", "tenant_api_service", "app/application/tenant_api.py", "code"),
    RequiredArtifact("enterprise_and_odoo", "tenant_api_guide", "docs/guide/20-odoo-api-cliente-empresarial.md", "doc"),
    RequiredArtifact("enterprise_and_odoo", "odoo15_localization", "integration/odoo/odoo15_getupsoft_do_localization/README.md", "addon"),
    RequiredArtifact("enterprise_and_odoo", "odoo19_localization", "integration/odoo/odoo19_getupsoft_do_localization/README.md", "addon"),
    RequiredArtifact("notifications", "email_service", "app/services/email_service.py", "code"),
    RequiredArtifact("notifications", "email_service_tests", "tests/test_email_service.py", "test"),
    RequiredArtifact("notifications", "email_service_guide", "docs/guide/19-email-smtp-service.md", "doc"),
    RequiredArtifact("compliance_and_runbooks", "sla_doc", "docs/compliance/SOPORTE_SLA.md", "doc"),
    RequiredArtifact("compliance_and_runbooks", "dgii_contact_doc", "docs/compliance/CONTACTO_DGII.md", "doc"),
    RequiredArtifact("compliance_and_runbooks", "real_certification_runbook", "scripts/automation/REAL_CERTIFICATION_RUNBOOK.md", "runbook"),
    RequiredArtifact("dgii_automation", "dgii_portal_automation_guide", "docs/guide/22-dgii-portal-automation.md", "doc"),
    RequiredArtifact("dgii_automation", "dgii_portal_automation_tests", "tests/test_dgii_portal_automation.py", "test"),
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Audita si las herramientas críticas del contexto de negocio están desarrolladas")
    parser.add_argument("--repo-root", default=os.getcwd(), help="Raíz del repo a revisar")
    parser.add_argument(
        "--write-report",
        action="store_true",
        help="Escribe el reporte en .ai_context/notes/business_context_readiness_report.json",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    report = assess_business_context_readiness(args.repo_root, write_report=args.write_report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "compliant" else 1


def assess_business_context_readiness(
    repo_root: str | Path | None = None,
    *,
    write_report: bool = False,
) -> dict[str, Any]:
    root = Path(repo_root or os.getcwd()).resolve()
    categories: dict[str, dict[str, Any]] = {}
    missing_required: list[str] = []
    items: list[dict[str, Any]] = []

    for artifact in REQUIRED_ARTIFACTS:
        path = root / artifact.path
        exists = path.exists()
        item = {
            "category": artifact.category,
            "name": artifact.name,
            "path": artifact.path,
            "kind": artifact.kind,
            "required": artifact.required,
            "exists": exists,
            "note": artifact.note,
        }
        items.append(item)

        bucket = categories.setdefault(
            artifact.category,
            {"required_total": 0, "present_total": 0, "missing": []},
        )
        if artifact.required:
            bucket["required_total"] += 1
            if exists:
                bucket["present_total"] += 1
            else:
                bucket["missing"].append(artifact.path)
                missing_required.append(artifact.path)

    status = "compliant" if not missing_required else "missing_tools"
    report: dict[str, Any] = {
        "status": status,
        "repo_root": str(root),
        "summary": {
            "required_total": sum(1 for artifact in REQUIRED_ARTIFACTS if artifact.required),
            "present_total": sum(1 for item in items if item["required"] and item["exists"]),
            "missing_total": len(missing_required),
        },
        "categories": categories,
        "missing_required": missing_required,
        "items": items,
    }
    if write_report:
        notes_dir = root / ".ai_context" / "notes"
        notes_dir.mkdir(parents=True, exist_ok=True)
        report_path = notes_dir / "business_context_readiness_report.json"
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        report["report_path"] = str(report_path)
    return report
