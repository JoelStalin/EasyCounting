"""Download handling with validation and traceability."""

from __future__ import annotations

from datetime import datetime
import hashlib
import mimetypes
from pathlib import Path
from typing import Any

from app.dgii_portal_automation.errors import DGIIDownloadError
from app.dgii_portal_automation.models import DownloadArtifact
from app.dgii_portal_automation.safety import ensure_authorized_domain, safe_logging
from app.dgii_portal_automation.ui import find_clickable


def download_file(
    runtime: Any,
    *,
    trigger_label: str | None = None,
    locator: Any | None = None,
    context: dict[str, str] | None = None,
) -> DownloadArtifact:
    page = runtime.ensure_page()
    if locator is None and trigger_label is None:
        raise DGIIDownloadError("Debes indicar trigger_label o locator para iniciar la descarga")
    if locator is None:
        locator = find_clickable(page, trigger_label or "")
    if locator is None:
        raise DGIIDownloadError(f"No se encontro un disparador de descarga para: {trigger_label}")

    href = None
    try:
        href = locator.first.get_attribute("href")
    except Exception:
        href = None
    if href:
        ensure_authorized_domain(href, allowed_domains=runtime.config.allowed_domains)

    safe_logging(runtime, "download.start", level="info", label=trigger_label, context=context or {})
    with page.expect_download(timeout=runtime.config.action_timeout_ms) as download_info:
        locator.first.click(timeout=runtime.config.action_timeout_ms)
    download = download_info.value
    suggested_name = download.suggested_filename or "download.bin"
    destination = rename_by_context(
        runtime.config.download_dir / suggested_name,
        context=context or {},
    )
    download.save_as(str(destination))
    artifact = validate_download(destination, label=trigger_label, source_url=href or runtime.current_url)
    register_download(runtime, artifact)
    return artifact


def validate_download(path: str | Path, *, label: str | None = None, source_url: str | None = None) -> DownloadArtifact:
    file_path = Path(path)
    if not file_path.exists() or not file_path.is_file():
        raise DGIIDownloadError(f"El archivo descargado no existe: {file_path}")
    size = file_path.stat().st_size
    if size <= 0:
        raise DGIIDownloadError(f"El archivo descargado esta vacio: {file_path}")
    return DownloadArtifact(
        path=file_path,
        filename=file_path.name,
        size_bytes=size,
        sha256=_sha256(file_path),
        content_type=mimetypes.guess_type(file_path.name)[0],
        source_url=source_url,
        label=label,
        downloaded_at=datetime.utcnow(),
    )


def rename_by_context(path: str | Path, *, context: dict[str, str] | None = None) -> Path:
    destination = Path(path)
    context = context or {}
    if not context:
        return destination
    stem = destination.stem
    suffix = destination.suffix
    parts = [stem]
    for key in sorted(context):
        value = _safe_filename_component(context[key])
        if value:
            parts.append(value)
    return destination.with_name("_".join(parts) + suffix)


def register_download(runtime: Any, artifact: DownloadArtifact) -> DownloadArtifact:
    runtime.register_download_artifact(artifact)
    safe_logging(
        runtime,
        "download.success",
        level="info",
        filename=artifact.filename,
        size_bytes=artifact.size_bytes,
        sha256=artifact.sha256,
        content_type=artifact.content_type,
        source_url=artifact.source_url,
        label=artifact.label,
    )
    return artifact


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8192), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _safe_filename_component(value: str | None) -> str:
    if not value:
        return ""
    cleaned = "".join(char if char.isalnum() or char in {"-", "_"} else "_" for char in value.strip())
    return cleaned.strip("_")
