from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field
from pydantic.config import ConfigDict


class BrowserMcpTimeouts(BaseModel):
    action_timeout_ms: int | None = Field(default=None, alias="actionTimeoutMs")
    navigation_timeout_ms: int | None = Field(default=None, alias="navigationTimeoutMs")

    model_config = ConfigDict(populate_by_name=True)


class BrowserMcpArtifacts(BaseModel):
    screenshot: bool | None = True
    pdf: bool | None = False
    snapshot: bool | None = True
    trace: bool | None = True
    save_session: bool | None = Field(default=False, alias="saveSession")

    model_config = ConfigDict(populate_by_name=True)


class BrowserMcpNetworkPolicy(BaseModel):
    allowed_origins: list[str] = Field(default_factory=list, alias="allowedOrigins")
    blocked_origins: list[str] = Field(default_factory=list, alias="blockedOrigins")
    mock_routes: list[dict[str, Any]] = Field(default_factory=list, alias="mockRoutes")

    model_config = ConfigDict(populate_by_name=True)


class BrowserMcpTarget(BaseModel):
    url: str | None = None
    html: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class BrowserMcpJobRequest(BaseModel):
    job_id: str | None = Field(default=None, alias="jobId")
    scenario: str
    browser: Literal["chromium", "firefox", "webkit"] | None = None
    mode: Literal["persistent_profile", "isolated_session", "cdp_attach"] = "isolated_session"
    headless: bool | None = None
    keep_open_on_failure: bool | None = Field(default=None, alias="keepOpenOnFailure")
    keep_open_on_success: bool | None = Field(default=None, alias="keepOpenOnSuccess")
    target: BrowserMcpTarget = Field(default_factory=BrowserMcpTarget)
    steps: list[dict[str, Any]] = Field(default_factory=list)
    session_ref: str | None = Field(default=None, alias="sessionRef")
    storage_state_path: str | None = Field(default=None, alias="storageStatePath")
    user_data_dir: str | None = Field(default=None, alias="userDataDir")
    save_session: bool | None = Field(default=None, alias="saveSession")
    output_dir: str | None = Field(default=None, alias="outputDir")
    cdp_url: str | None = Field(default=None, alias="cdpEndpoint")
    timeouts: BrowserMcpTimeouts = Field(default_factory=BrowserMcpTimeouts)
    artifacts: BrowserMcpArtifacts = Field(default_factory=BrowserMcpArtifacts)
    network_policy: BrowserMcpNetworkPolicy = Field(default_factory=BrowserMcpNetworkPolicy, alias="networkPolicy")

    model_config = ConfigDict(populate_by_name=True)


class BrowserMcpJobResponse(BaseModel):
    job_id: str = Field(alias="jobId")
    status: str
    final_url: str | None = Field(default=None, alias="finalUrl")
    session_ref: str | None = Field(default=None, alias="sessionRef")
    artifacts: list[str] = Field(default_factory=list)
    result: dict[str, Any] = Field(default_factory=dict)
    network_summary: dict[str, Any] = Field(default_factory=dict, alias="networkSummary")
    console_summary: dict[str, Any] = Field(default_factory=dict, alias="consoleSummary")
    step_results: list[dict[str, Any]] = Field(default_factory=list, alias="stepResults")
    error: str | dict[str, Any] | None = None

    model_config = ConfigDict(populate_by_name=True)


class BrowserMcpClientSettings(BaseModel):
    enabled: bool
    mode: Literal["remote", "stdio"]
    base_url: str
    stdio_cmd: str
    remote_timeout_seconds: float
    default_browser: Literal["chromium", "firefox", "webkit"]
    default_headless: bool
    output_root: Path
    allowed_origins: list[str]
    blocked_origins: list[str]
    action_timeout_ms: int
    navigation_timeout_ms: int
    save_session_default: bool
    trace_default: bool
    pdf_default: bool
    screenshot_default: bool
