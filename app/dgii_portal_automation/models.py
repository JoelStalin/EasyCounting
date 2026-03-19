"""Data models used by the DGII automation toolkit."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class DownloadLink:
    label: str
    url: str | None = None
    selector_hint: str | None = None


@dataclass(slots=True)
class DownloadArtifact:
    path: Path
    filename: str
    size_bytes: int
    sha256: str
    content_type: str | None
    source_url: str | None
    label: str | None
    downloaded_at: datetime


@dataclass(slots=True)
class SensitiveAction:
    action_type: str
    label: str
    reason: str
    risk: str
    current_url: str | None = None
    details: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class AuditEvent:
    timestamp: str
    level: str
    event: str
    details: dict[str, Any]


@dataclass(slots=True)
class StructuredTable:
    name: str | None
    rows: list[dict[str, str]]
    headers: list[str]
    pages_read: int = 1


@dataclass(slots=True)
class ExtractionResult:
    url: str
    tables: list[StructuredTable] = field(default_factory=list)
    fields: dict[str, str] = field(default_factory=dict)
    messages: list[str] = field(default_factory=list)
    download_links: list[DownloadLink] = field(default_factory=list)


@dataclass(slots=True)
class TaskResult:
    task_name: str
    url: str
    extraction: ExtractionResult
    downloads: list[DownloadArtifact] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
