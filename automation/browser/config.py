"""Feature-flagged browser automation configuration."""
from __future__ import annotations

from dataclasses import dataclass

from app.infra.settings import settings


@dataclass(slots=True)
class BrowserAutomationSettings:
    enabled: bool
    mode: str

    @classmethod
    def from_settings(cls) -> "BrowserAutomationSettings":
        return cls(
            enabled=bool(settings.dgii_browser_automation_enabled),
            mode=settings.dgii_browser_automation_mode,
        )

    def ensure_enabled(self) -> None:
        if not self.enabled:
            raise RuntimeError("DGII browser automation is disabled by feature flag")

