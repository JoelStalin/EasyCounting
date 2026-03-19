"""Central configuration for DGII web automation."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import os
from pathlib import Path
from typing import Iterable
from urllib.parse import urlparse

from app.dgii_portal_automation.errors import DGIIConfigurationError


class ExecutionMode(str, Enum):
    READ_ONLY = "read_only"
    ASSISTED = "assisted"


@dataclass(slots=True)
class RetryPolicy:
    attempts: int = 3
    base_delay_seconds: float = 1.0
    max_delay_seconds: float = 5.0


@dataclass(slots=True)
class ExportSettings:
    json_indent: int = 2
    csv_encoding: str = "utf-8"
    excel_sheet_name: str = "DGII"


@dataclass(slots=True)
class DGIIAutomationConfig:
    base_url: str
    login_url: str
    username: str | None
    password: str | None
    mode: ExecutionMode = ExecutionMode.READ_ONLY
    allowed_domains: tuple[str, ...] = ("dgii.gov.do", "www.dgii.gov.do", "ecf.dgii.gov.do", "fc.dgii.gov.do")
    headless: bool = True
    browser_name: str = "chromium"
    browser_channel: str | None = None
    timeout_ms: int = 30_000
    navigation_timeout_ms: int = 45_000
    action_timeout_ms: int = 20_000
    slow_mo_ms: int = 0
    download_dir: Path = field(default_factory=lambda: Path("artifacts_live_dns/dgii_portal/downloads"))
    export_dir: Path = field(default_factory=lambda: Path("artifacts_live_dns/dgii_portal/exports"))
    audit_dir: Path = field(default_factory=lambda: Path("artifacts_live_dns/dgii_portal/audit"))
    screenshot_dir: Path = field(default_factory=lambda: Path("artifacts_live_dns/dgii_portal/screenshots"))
    retry_policy: RetryPolicy = field(default_factory=RetryPolicy)
    export: ExportSettings = field(default_factory=ExportSettings)
    screenshot_blur_radius: int = 10
    max_table_pages: int = 10

    def __post_init__(self) -> None:
        self.base_url = self.base_url.strip()
        self.login_url = self.login_url.strip()
        if not self.base_url or not self.login_url:
            raise DGIIConfigurationError("DGII_PORTAL_BASE_URL y DGII_PORTAL_LOGIN_URL son obligatorios")
        if not self._is_authorized_url(self.base_url):
            raise DGIIConfigurationError("DGII_PORTAL_BASE_URL debe apuntar a un dominio autorizado de la DGII")
        if not self._is_authorized_url(self.login_url):
            raise DGIIConfigurationError("DGII_PORTAL_LOGIN_URL debe apuntar a un dominio autorizado de la DGII")
        self.download_dir.mkdir(parents=True, exist_ok=True)
        self.export_dir.mkdir(parents=True, exist_ok=True)
        self.audit_dir.mkdir(parents=True, exist_ok=True)
        self.screenshot_dir.mkdir(parents=True, exist_ok=True)

    @classmethod
    def from_env(cls) -> "DGIIAutomationConfig":
        mode_raw = os.getenv("DGII_PORTAL_MODE", ExecutionMode.READ_ONLY.value).strip().lower()
        try:
            mode = ExecutionMode(mode_raw)
        except ValueError as exc:
            raise DGIIConfigurationError("DGII_PORTAL_MODE debe ser read_only o assisted") from exc

        allowed_domains = tuple(
            domain.strip().lower()
            for domain in os.getenv(
                "DGII_PORTAL_ALLOWED_DOMAINS",
                "dgii.gov.do,www.dgii.gov.do,ecf.dgii.gov.do,fc.dgii.gov.do",
            ).split(",")
            if domain.strip()
        )
        return cls(
            base_url=os.getenv("DGII_PORTAL_BASE_URL", "https://dgii.gov.do"),
            login_url=os.getenv("DGII_PORTAL_LOGIN_URL", "https://dgii.gov.do/OFV/home.aspx"),
            username=os.getenv("DGII_PORTAL_USERNAME") or None,
            password=os.getenv("DGII_PORTAL_PASSWORD") or None,
            mode=mode,
            allowed_domains=allowed_domains,
            headless=_bool_env("DGII_PORTAL_HEADLESS", True),
            browser_name=os.getenv("DGII_PORTAL_BROWSER", "chromium").strip().lower() or "chromium",
            browser_channel=os.getenv("DGII_PORTAL_BROWSER_CHANNEL") or None,
            timeout_ms=int(os.getenv("DGII_PORTAL_TIMEOUT_MS", "30000")),
            navigation_timeout_ms=int(os.getenv("DGII_PORTAL_NAV_TIMEOUT_MS", "45000")),
            action_timeout_ms=int(os.getenv("DGII_PORTAL_ACTION_TIMEOUT_MS", "20000")),
            slow_mo_ms=int(os.getenv("DGII_PORTAL_SLOW_MO_MS", "0")),
            download_dir=Path(os.getenv("DGII_PORTAL_DOWNLOAD_DIR", "artifacts_live_dns/dgii_portal/downloads")),
            export_dir=Path(os.getenv("DGII_PORTAL_EXPORT_DIR", "artifacts_live_dns/dgii_portal/exports")),
            audit_dir=Path(os.getenv("DGII_PORTAL_AUDIT_DIR", "artifacts_live_dns/dgii_portal/audit")),
            screenshot_dir=Path(
                os.getenv("DGII_PORTAL_SCREENSHOT_DIR", "artifacts_live_dns/dgii_portal/screenshots")
            ),
            retry_policy=RetryPolicy(
                attempts=int(os.getenv("DGII_PORTAL_RETRY_ATTEMPTS", "3")),
                base_delay_seconds=float(os.getenv("DGII_PORTAL_RETRY_BASE_DELAY", "1.0")),
                max_delay_seconds=float(os.getenv("DGII_PORTAL_RETRY_MAX_DELAY", "5.0")),
            ),
            export=ExportSettings(
                json_indent=int(os.getenv("DGII_PORTAL_JSON_INDENT", "2")),
                csv_encoding=os.getenv("DGII_PORTAL_CSV_ENCODING", "utf-8"),
                excel_sheet_name=os.getenv("DGII_PORTAL_EXCEL_SHEET", "DGII"),
            ),
            screenshot_blur_radius=int(os.getenv("DGII_PORTAL_SCREENSHOT_BLUR_RADIUS", "10")),
            max_table_pages=int(os.getenv("DGII_PORTAL_MAX_TABLE_PAGES", "10")),
        )

    def ensure_credentials(self) -> None:
        if not self.username or not self.password:
            raise DGIIConfigurationError(
                "DGII_PORTAL_USERNAME y DGII_PORTAL_PASSWORD son obligatorios para autenticarse"
            )

    def is_authorized_url(self, url: str) -> bool:
        return self._is_authorized_url(url)

    def sanitize_allowed_domains(self, values: Iterable[str]) -> tuple[str, ...]:
        return tuple(item.strip().lower() for item in values if item and item.strip())

    def _is_authorized_url(self, url: str) -> bool:
        parsed = urlparse(url)
        host = (parsed.hostname or "").lower()
        return bool(host) and any(host == domain or host.endswith(f".{domain}") for domain in self.allowed_domains)


def _bool_env(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}
