from __future__ import annotations

from pathlib import Path

from app.services.browser_mcp.schemas import BrowserMcpClientSettings, BrowserMcpJobRequest


def resolve_output_dir(settings: BrowserMcpClientSettings, job: BrowserMcpJobRequest) -> Path:
    if job.output_dir:
        return Path(job.output_dir)
    job_id = job.job_id or "browser-job"
    return settings.output_root / job.scenario / job_id


def normalize_artifact_paths(paths: list[str]) -> list[str]:
    normalized: list[str] = []
    for item in paths:
        try:
            normalized.append(str(Path(item).resolve()))
        except OSError:
            normalized.append(item)
    return normalized

