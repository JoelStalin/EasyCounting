"""Controlled browser workflow for DGII evidence capture."""
from __future__ import annotations

from pathlib import Path

from automation.browser.config import BrowserAutomationSettings
from automation.browser.drivers.playwright_driver import build_runtime
from automation.browser.evidence.collector import evidence_directory


def capture_portal_evidence(operation_id: str) -> dict[str, str]:
    config = BrowserAutomationSettings.from_settings()
    config.ensure_enabled()
    target_dir: Path = evidence_directory(operation_id)
    with build_runtime() as runtime:
        page = runtime.ensure_page()
        page.goto(runtime.config.login_url)
        screenshot = target_dir / "login-page.png"
        page.screenshot(path=str(screenshot), full_page=True)
        runtime.record_event("browser.evidence.captured", operation_id=operation_id, screenshot=str(screenshot))
    return {"operation_id": operation_id, "screenshot": str(screenshot), "mode": config.mode}

