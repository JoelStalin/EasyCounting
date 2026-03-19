from __future__ import annotations

import json
from pathlib import Path

from app.business_context.readiness import assess_business_context_readiness


def _touch(base: Path, relative_path: str) -> None:
    target = base / relative_path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("ok", encoding="utf-8")


def test_business_context_readiness_is_compliant_when_manifest_is_present(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    required_paths = [
        "docs/business/2026-03-19_auditoria_repositorio_mercado_pricing.md",
        ".ai_context/notes/2026-03-19_repo_market_pricing_audit.md",
        ".ai_context/notes/LONG_TERM_PROMPT_MEMORY.md",
        ".ai_context/notes/chat_memory_policy.json",
        ".ai_context/notes/prompt_catalog.json",
        ".ai_context/notes/prompt_dictionary.json",
        "scripts/automation/save_chat_history.py",
        "scripts/automation/close_project_chat_session.py",
        "scripts/automation/check_chat_memory_compliance.py",
        "tests/test_chat_memory.py",
        "docs/guide/13-planes-tarifas.md",
        "app/models/billing.py",
        "app/application/recurring_invoices.py",
        "tests/test_recurring_invoices.py",
        "scripts/automation/setup_demo_environment.py",
        "scripts/automation/seed_public_demo_data.py",
        "frontend/apps/corporate-portal/index.html",
        "frontend/apps/seller-portal/src/pages/Login.tsx",
        "app/application/tenant_api.py",
        "docs/guide/20-odoo-api-cliente-empresarial.md",
        "integration/odoo/odoo15_getupsoft_do_localization/README.md",
        "integration/odoo/odoo19_getupsoft_do_localization/README.md",
        "app/services/email_service.py",
        "tests/test_email_service.py",
        "docs/guide/19-email-smtp-service.md",
        "docs/compliance/SOPORTE_SLA.md",
        "docs/compliance/CONTACTO_DGII.md",
        "scripts/automation/REAL_CERTIFICATION_RUNBOOK.md",
        "docs/guide/22-dgii-portal-automation.md",
        "tests/test_dgii_portal_automation.py",
    ]
    for path in required_paths:
        _touch(repo_root, path)

    report = assess_business_context_readiness(repo_root, write_report=True)

    assert report["status"] == "compliant"
    assert report["summary"]["missing_total"] == 0
    report_path = repo_root / ".ai_context" / "notes" / "business_context_readiness_report.json"
    assert report_path.exists()
    payload = json.loads(report_path.read_text(encoding="utf-8"))
    assert payload["status"] == "compliant"


def test_business_context_readiness_reports_missing_required_items(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    _touch(repo_root, "docs/business/2026-03-19_auditoria_repositorio_mercado_pricing.md")

    report = assess_business_context_readiness(repo_root)

    assert report["status"] == "missing_tools"
    assert report["summary"]["missing_total"] > 0
    assert ".ai_context/notes/LONG_TERM_PROMPT_MEMORY.md" in report["missing_required"]
