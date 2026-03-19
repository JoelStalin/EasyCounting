from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.dgii_portal_automation.config import DGIIAutomationConfig, ExecutionMode
from app.dgii_portal_automation.models import AuditEvent, SensitiveAction
from app.dgii_portal_automation.reporting import build_csv_report, build_json_report, generate_audit_trace
from app.dgii_portal_automation.safety import detect_sensitive_action, redact_secrets, request_confirmation


class _FakeRuntime:
    def __init__(self) -> None:
        self.current_url = "https://dgii.gov.do/OFV/home.aspx"
        self.audit_events = [
            AuditEvent(timestamp="2026-03-19T00:00:00+00:00", level="info", event="demo", details={"ok": True})
        ]
        self.downloads = []


def _config(tmp_path: Path) -> DGIIAutomationConfig:
    return DGIIAutomationConfig(
        base_url="https://dgii.gov.do",
        login_url="https://dgii.gov.do/OFV/home.aspx",
        username="user@example.com",
        password="secret-password",
        mode=ExecutionMode.READ_ONLY,
        download_dir=tmp_path / "downloads",
        export_dir=tmp_path / "exports",
        audit_dir=tmp_path / "audit",
        screenshot_dir=tmp_path / "screenshots",
    )


def test_redact_secrets_hides_known_values() -> None:
    payload = {
        "message": "Bearer abc.def.ghi",
        "cookie": "Cookie: sessionid=123",
        "url": "https://dgii.gov.do/test?token=plain",
        "user": "demo@example.com",
    }
    sanitized = redact_secrets(payload, secrets=["demo@example.com", "plain"])
    assert sanitized["user"] == "***REDACTED***"
    assert "***REDACTED***" in sanitized["message"]
    assert "***REDACTED***" in sanitized["cookie"]
    assert "***REDACTED***" in sanitized["url"]


def test_detect_sensitive_action_flags_declaration() -> None:
    action = detect_sensitive_action("Enviar declaracion", current_url="https://dgii.gov.do/ofv/declarar")
    assert action is not None
    assert action.action_type == "declaracion"


def test_request_confirmation_blocks_in_read_only() -> None:
    action = SensitiveAction(
        action_type="envio",
        label="Enviar",
        reason="Accion sensible",
        risk="alto",
    )
    with pytest.raises(Exception):
        request_confirmation(action, mode=ExecutionMode.READ_ONLY)


def test_request_confirmation_allows_assisted_callback() -> None:
    action = SensitiveAction(
        action_type="envio",
        label="Enviar",
        reason="Accion sensible",
        risk="alto",
    )
    approved = request_confirmation(action, mode=ExecutionMode.ASSISTED, confirmation_callback=lambda _: True)
    assert approved is True


def test_build_reports_and_audit_trace(tmp_path: Path) -> None:
    payload = [{"rnc": "22500706423", "estado": "ACTIVO"}]
    json_path = build_json_report(payload, tmp_path / "result.json")
    csv_path = build_csv_report(payload, tmp_path / "result.csv")
    assert json_path.exists()
    assert csv_path.exists()
    audit_path = generate_audit_trace(_FakeRuntime(), tmp_path / "audit.json")
    parsed = json.loads(audit_path.read_text(encoding="utf-8"))
    assert parsed["current_url"] == "https://dgii.gov.do/OFV/home.aspx"
    assert parsed["audit_events"][0]["event"] == "demo"


def test_config_creates_directories(tmp_path: Path) -> None:
    config = _config(tmp_path)
    assert config.download_dir.exists()
    assert config.export_dir.exists()
    assert config.audit_dir.exists()
    assert config.screenshot_dir.exists()
