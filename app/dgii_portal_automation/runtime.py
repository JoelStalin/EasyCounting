"""Runtime wrapper around Playwright objects and audit trace."""

from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
from typing import Any

from app.dgii_portal_automation.config import DGIIAutomationConfig
from app.dgii_portal_automation.errors import DGIIConfigurationError
from app.dgii_portal_automation.models import AuditEvent, DownloadArtifact


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_playwright_sync() -> Any:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:  # pragma: no cover - dependency guard
        raise DGIIConfigurationError(
            "Playwright no esta instalado. Instala playwright y ejecuta 'playwright install chromium'."
        ) from exc
    return sync_playwright


class AutomationRuntime:
    """Holds browser state, page objects and a sanitized audit trace."""

    def __init__(self, config: DGIIAutomationConfig) -> None:
        self.config = config
        self.audit_events: list[AuditEvent] = []
        self.downloads: list[DownloadArtifact] = []
        self._playwright_manager: Any | None = None
        self.playwright: Any | None = None
        self.browser: Any | None = None
        self.context: Any | None = None
        self.page: Any | None = None

    def start(self) -> "AutomationRuntime":
        sync_playwright = _load_playwright_sync()
        self._playwright_manager = sync_playwright().start()
        browser_type = getattr(self._playwright_manager, self.config.browser_name, None)
        if browser_type is None:
            raise DGIIConfigurationError(f"Navegador no soportado: {self.config.browser_name}")
        launch_kwargs: dict[str, Any] = {
            "headless": self.config.headless,
            "slow_mo": self.config.slow_mo_ms,
        }
        if self.config.browser_channel:
            launch_kwargs["channel"] = self.config.browser_channel
        self.browser = browser_type.launch(**launch_kwargs)
        self.context = self.browser.new_context(
            accept_downloads=True,
            ignore_https_errors=False,
        )
        self.page = self.context.new_page()
        self.page.set_default_timeout(self.config.timeout_ms)
        self.page.set_default_navigation_timeout(self.config.navigation_timeout_ms)
        self.record_event("runtime.start", level="info", browser=self.config.browser_name, headless=self.config.headless)
        return self

    def close(self) -> None:
        self.record_event("runtime.stop", level="info", current_url=self.current_url)
        if self.page is not None:
            self.page.close()
        if self.context is not None:
            self.context.close()
        if self.browser is not None:
            self.browser.close()
        if self._playwright_manager is not None:
            self._playwright_manager.stop()
        self.page = None
        self.context = None
        self.browser = None
        self.playwright = None
        self._playwright_manager = None

    def __enter__(self) -> "AutomationRuntime":
        return self.start()

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    @property
    def current_url(self) -> str | None:
        if self.page is None:
            return None
        try:
            return str(self.page.url)
        except Exception:  # pragma: no cover - defensive
            return None

    def ensure_page(self) -> Any:
        if self.page is None:
            raise DGIIConfigurationError("La sesion Playwright no esta iniciada")
        return self.page

    def ensure_authorized_url(self, url: str) -> str:
        if not self.config.is_authorized_url(url):
            raise DGIIConfigurationError(f"URL fuera de dominio autorizado: {url}")
        return url

    def record_event(self, event: str, *, level: str = "info", **details: Any) -> None:
        self.audit_events.append(
            AuditEvent(
                timestamp=_utcnow_iso(),
                level=level,
                event=event,
                details=details,
            )
        )

    def register_download_artifact(self, artifact: DownloadArtifact) -> None:
        self.downloads.append(artifact)
        self.record_event("download.registered", level="info", **asdict(artifact))
