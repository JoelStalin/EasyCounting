from __future__ import annotations

import subprocess

import httpx
import respx

from app.infra.settings import settings
from app.services.browser_mcp.client import BrowserMcpRemoteClient, BrowserMcpStdioClient, build_browser_mcp_settings
from app.services.browser_mcp.orchestrator import prepare_browser_job
from app.services.browser_mcp.schemas import BrowserMcpJobRequest


def test_prepare_browser_job_applies_defaults_and_generates_job_id(monkeypatch) -> None:
    monkeypatch.setattr(settings, "browser_mcp_default_browser", "chromium")
    monkeypatch.setattr(settings, "browser_mcp_default_headless", True)
    monkeypatch.setattr(settings, "browser_mcp_save_session_default", True)
    monkeypatch.setattr(settings, "browser_mcp_action_timeout_ms", 11111)
    monkeypatch.setattr(settings, "browser_mcp_navigation_timeout_ms", 22222)
    monkeypatch.setattr(settings, "browser_mcp_trace_default", True)
    monkeypatch.setattr(settings, "browser_mcp_pdf_default", False)
    monkeypatch.setattr(settings, "browser_mcp_screenshot_default", True)
    monkeypatch.setattr(settings, "browser_mcp_output_root", settings.browser_mcp_output_root)
    monkeypatch.setattr(settings, "browser_mcp_allowed_origins_raw", "https://example.com")
    monkeypatch.setattr(settings, "browser_mcp_blocked_origins_raw", "https://blocked.example.com")

    prepared = prepare_browser_job(BrowserMcpJobRequest(scenario="open-url-extract"))

    assert prepared.job_id is not None
    assert prepared.browser == "chromium"
    assert prepared.headless is True
    assert prepared.save_session is True
    assert prepared.timeouts.action_timeout_ms == 11111
    assert prepared.timeouts.navigation_timeout_ms == 22222
    assert prepared.artifacts.trace is True
    assert prepared.artifacts.pdf is False
    assert prepared.artifacts.screenshot is True
    assert prepared.network_policy.allowed_origins == ["https://example.com"]
    assert prepared.network_policy.blocked_origins == ["https://blocked.example.com"]
    assert prepared.output_dir


@respx.mock
def test_remote_client_runs_sync(monkeypatch) -> None:
    monkeypatch.setattr(settings, "browser_mcp_enabled", True)
    monkeypatch.setattr(settings, "browser_mcp_mode", "remote")
    monkeypatch.setattr(settings, "browser_mcp_base_url", "http://browser-mcp:8930")
    monkeypatch.setattr(settings, "browser_mcp_remote_timeout_seconds", 5.0)

    route = respx.post("http://browser-mcp:8930/api/v1/jobs/run-sync").mock(
        return_value=httpx.Response(
            200,
            json={
                "jobId": "job-1",
                "status": "completed",
                "artifacts": ["tests/artifacts/browser-mcp/job-1/run.json"],
                "networkSummary": {"requests": 1},
                "consoleSummary": {},
                "stepResults": [],
            },
        )
    )

    client = BrowserMcpRemoteClient(build_browser_mcp_settings())
    response = client.run_sync(BrowserMcpJobRequest(jobId="job-1", scenario="open-url-extract"))

    assert route.called
    assert response.job_id == "job-1"
    assert response.status == "completed"


@respx.mock
def test_remote_client_returns_failed_job_response_on_http_500(monkeypatch) -> None:
    monkeypatch.setattr(settings, "browser_mcp_enabled", True)
    monkeypatch.setattr(settings, "browser_mcp_mode", "remote")
    monkeypatch.setattr(settings, "browser_mcp_base_url", "http://browser-mcp:8930")
    monkeypatch.setattr(settings, "browser_mcp_remote_timeout_seconds", 5.0)

    respx.post("http://browser-mcp:8930/api/v1/jobs/run-sync").mock(
        return_value=httpx.Response(
            500,
            json={
                "jobId": "job-failed",
                "status": "failed",
                "artifacts": ["tests/artifacts/browser-mcp/job-failed/run.json"],
                "networkSummary": {"requests": 10},
                "consoleSummary": {"warning": 2},
                "stepResults": [],
                "error": "stuck",
            },
        )
    )

    client = BrowserMcpRemoteClient(build_browser_mcp_settings())
    response = client.run_sync(BrowserMcpJobRequest(jobId="job-failed", scenario="open-url-extract"))

    assert response.job_id == "job-failed"
    assert response.status == "failed"


def test_stdio_client_runs_sync(monkeypatch) -> None:
    monkeypatch.setattr(settings, "browser_mcp_enabled", True)
    monkeypatch.setattr(settings, "browser_mcp_mode", "stdio")
    monkeypatch.setattr(settings, "browser_mcp_stdio_cmd", "node automation/browser-mcp/dist/cli/run-job.js")

    completed = subprocess.CompletedProcess(
        args=["node"],
        returncode=0,
        stdout=(
            '{"jobId":"job-stdio","status":"completed","artifacts":[],"networkSummary":{},'
            '"consoleSummary":{},"stepResults":[]}\n'
        ),
        stderr="",
    )

    monkeypatch.setattr(subprocess, "run", lambda *args, **kwargs: completed)

    client = BrowserMcpStdioClient(build_browser_mcp_settings())
    response = client.run_sync(BrowserMcpJobRequest(jobId="job-stdio", scenario="open-url-extract"))

    assert response.job_id == "job-stdio"
    assert response.status == "completed"
