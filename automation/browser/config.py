"""Feature-flagged browser automation configuration."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from app.infra.settings import settings

# Canonical automation modes
EVIDENCE_ONLY = "evidence-only"
ASSISTIVE = "assistive"
FULL = "full"

ALLOWED_MODES = {EVIDENCE_ONLY, ASSISTIVE, FULL}

# Modes that permit write/submit actions on the DGII portal
WRITE_PERMITTED_MODES = {FULL}

# Modes that permit assistive (read + guided) actions
ASSISTIVE_PERMITTED_MODES = {ASSISTIVE, FULL}


@dataclass(slots=True)
class BrowserAutomationSettings:
    enabled: bool
    mode: str

    @classmethod
    def from_settings(cls) -> "BrowserAutomationSettings":
        raw_mode = (settings.dgii_browser_automation_mode or EVIDENCE_ONLY).strip().lower()
        # Normalize and validate mode; default to evidence-only if unknown
        if raw_mode not in ALLOWED_MODES:
            raw_mode = EVIDENCE_ONLY
        return cls(
            enabled=bool(settings.dgii_browser_automation_enabled),
            mode=raw_mode,
        )

    # ------------------------------------------------------------------
    # Guards
    # ------------------------------------------------------------------

    def ensure_enabled(self) -> None:
        """Raise if browser automation is disabled by feature flag."""
        if not self.enabled:
            raise RuntimeError(
                "DGII browser automation is disabled by feature flag "
                "(DGII_BROWSER_AUTOMATION_ENABLED=false)"
            )

    def ensure_evidence_only_mode(self) -> None:
        """
        Raise if the current mode is NOT evidence-only.
        Use this guard at the entry point of any workflow that must
        never submit data to the DGII portal.
        """
        self.ensure_enabled()
        if self.mode != EVIDENCE_ONLY:
            raise RuntimeError(
                f"Expected evidence-only mode but current mode is '{self.mode}'. "
                "Set DGII_BROWSER_AUTOMATION_MODE=evidence-only to proceed."
            )

    def ensure_assistive_or_evidence(self) -> None:
        """
        Raise if the current mode permits full write actions.
        Allows evidence-only and assistive modes only.
        """
        self.ensure_enabled()
        if self.mode in WRITE_PERMITTED_MODES:
            raise RuntimeError(
                f"Mode '{self.mode}' permits write actions. "
                "This guard requires evidence-only or assistive mode."
            )

    def assert_no_write_actions(self, action_description: str = "write action") -> None:
        """
        Raise if the current mode would allow submitting data to DGII.
        Call this before any click/submit that modifies portal state.
        """
        self.ensure_enabled()
        if self.mode in WRITE_PERMITTED_MODES:
            raise RuntimeError(
                f"Attempted '{action_description}' in mode '{self.mode}'. "
                "Write actions are blocked in evidence-only and assistive modes. "
                "Set DGII_BROWSER_AUTOMATION_MODE=full to enable (requires explicit authorization)."
            )

    @property
    def is_evidence_only(self) -> bool:
        return self.mode == EVIDENCE_ONLY

    @property
    def is_assistive(self) -> bool:
        return self.mode in ASSISTIVE_PERMITTED_MODES

    @property
    def writes_permitted(self) -> bool:
        return self.mode in WRITE_PERMITTED_MODES

    def __str__(self) -> str:
        status = "enabled" if self.enabled else "disabled"
        return f"BrowserAutomation({status}, mode={self.mode})"

