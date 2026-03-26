"""Thin wrapper over the existing Playwright runtime."""
from __future__ import annotations

from app.dgii_portal_automation.config import DGIIAutomationConfig
from app.dgii_portal_automation.runtime import AutomationRuntime


def build_runtime() -> AutomationRuntime:
    return AutomationRuntime(DGIIAutomationConfig.from_env())

