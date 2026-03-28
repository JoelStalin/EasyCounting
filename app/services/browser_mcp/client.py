from __future__ import annotations

import json
import shlex
import subprocess
from dataclasses import dataclass

import httpx

from app.infra.settings import settings
from app.services.browser_mcp.schemas import BrowserMcpClientSettings, BrowserMcpJobRequest, BrowserMcpJobResponse


class BrowserMcpClientError(RuntimeError):
    """Raised when the browser sidecar fails."""


def build_browser_mcp_settings() -> BrowserMcpClientSettings:
    return BrowserMcpClientSettings(
        enabled=settings.browser_mcp_enabled,
        mode=settings.browser_mcp_mode,
        base_url=settings.browser_mcp_base_url.rstrip("/"),
        stdio_cmd=settings.browser_mcp_stdio_cmd,
        remote_timeout_seconds=settings.browser_mcp_remote_timeout_seconds,
        default_browser=settings.browser_mcp_default_browser,
        default_headless=settings.browser_mcp_default_headless,
        output_root=settings.browser_mcp_output_root,
        allowed_origins=settings.browser_mcp_allowed_origins,
        blocked_origins=settings.browser_mcp_blocked_origins,
        action_timeout_ms=settings.browser_mcp_action_timeout_ms,
        navigation_timeout_ms=settings.browser_mcp_navigation_timeout_ms,
        save_session_default=settings.browser_mcp_save_session_default,
        trace_default=settings.browser_mcp_trace_default,
        pdf_default=settings.browser_mcp_pdf_default,
        screenshot_default=settings.browser_mcp_screenshot_default,
    )


@dataclass(slots=True)
class BrowserMcpRemoteClient:
    config: BrowserMcpClientSettings

    def run_sync(self, job: BrowserMcpJobRequest) -> BrowserMcpJobResponse:
        payload = job.model_dump(by_alias=True, exclude_none=True)
        with httpx.Client(timeout=self.config.remote_timeout_seconds) as client:
            response = client.post(f"{self.config.base_url}/api/v1/jobs/run-sync", json=payload)
        try:
            parsed = response.json()
        except ValueError:
            parsed = None
        if response.status_code >= 400:
            if isinstance(parsed, dict) and {"jobId", "status", "artifacts"}.issubset(parsed):
                return BrowserMcpJobResponse.model_validate(parsed)
            raise BrowserMcpClientError(f"Browser MCP remote error {response.status_code}: {response.text}")
        return BrowserMcpJobResponse.model_validate(parsed)

    def release_runtime(self, job_id: str) -> bool:
        with httpx.Client(timeout=self.config.remote_timeout_seconds) as client:
            response = client.delete(f"{self.config.base_url}/api/v1/jobs/{job_id}/runtime")
        if response.status_code >= 400:
            raise BrowserMcpClientError(f"Browser MCP runtime release error {response.status_code}: {response.text}")
        parsed = response.json()
        return bool(parsed.get("released"))


@dataclass(slots=True)
class BrowserMcpStdioClient:
    config: BrowserMcpClientSettings

    def run_sync(self, job: BrowserMcpJobRequest) -> BrowserMcpJobResponse:
        payload = json.dumps(job.model_dump(by_alias=True, exclude_none=True), ensure_ascii=False)
        proc = subprocess.run(
            shlex.split(self.config.stdio_cmd, posix=False),
            input=payload,
            capture_output=True,
            text=True,
            check=False,
        )
        if proc.returncode != 0:
            raise BrowserMcpClientError(
                f"Browser MCP stdio error {proc.returncode}: {(proc.stderr or proc.stdout).strip()}"
            )
        raw = (proc.stdout or "").strip()
        if not raw:
            raise BrowserMcpClientError("Browser MCP stdio returned empty output")
        return BrowserMcpJobResponse.model_validate_json(raw)


def get_browser_mcp_client() -> BrowserMcpRemoteClient | BrowserMcpStdioClient:
    config = build_browser_mcp_settings()
    if not config.enabled:
        raise BrowserMcpClientError("Browser MCP is disabled by configuration")
    if config.mode == "stdio":
        return BrowserMcpStdioClient(config)
    return BrowserMcpRemoteClient(config)
