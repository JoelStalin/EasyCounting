from __future__ import annotations

from uuid import uuid4

from app.services.browser_mcp.artifacts import normalize_artifact_paths, resolve_output_dir
from app.services.browser_mcp.client import build_browser_mcp_settings, get_browser_mcp_client
from app.services.browser_mcp.schemas import BrowserMcpJobRequest, BrowserMcpJobResponse


def prepare_browser_job(job: BrowserMcpJobRequest) -> BrowserMcpJobRequest:
    config = build_browser_mcp_settings()
    job.job_id = job.job_id or f"browser-job-{uuid4().hex}"
    job.browser = job.browser or config.default_browser
    job.headless = config.default_headless if job.headless is None else job.headless
    job.save_session = config.save_session_default if job.save_session is None else job.save_session
    job.timeouts.action_timeout_ms = job.timeouts.action_timeout_ms or config.action_timeout_ms
    job.timeouts.navigation_timeout_ms = job.timeouts.navigation_timeout_ms or config.navigation_timeout_ms
    job.artifacts.trace = config.trace_default if job.artifacts.trace is None else job.artifacts.trace
    job.artifacts.pdf = config.pdf_default if job.artifacts.pdf is None else job.artifacts.pdf
    job.artifacts.screenshot = (
        config.screenshot_default if job.artifacts.screenshot is None else job.artifacts.screenshot
    )
    if not job.network_policy.allowed_origins:
        job.network_policy.allowed_origins = list(config.allowed_origins)
    if not job.network_policy.blocked_origins:
        job.network_policy.blocked_origins = list(config.blocked_origins)
    if not job.output_dir:
        job.output_dir = str(resolve_output_dir(config, job))
    return job


def run_browser_job(job: BrowserMcpJobRequest) -> BrowserMcpJobResponse:
    prepared = prepare_browser_job(job)
    client = get_browser_mcp_client()
    response = client.run_sync(prepared)
    response.artifacts = normalize_artifact_paths(response.artifacts)
    return response
