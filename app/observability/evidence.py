"""Helpers to persist reproducible evidence artifacts."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from app.infra.settings import settings


def ensure_artifacts_root() -> Path:
    root = Path(settings.artifacts_root)
    root.mkdir(parents=True, exist_ok=True)
    return root


def build_run_directory(prefix: str = "") -> Path:
    root = ensure_artifacts_root()
    stamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    dirname = f"{stamp}_{prefix}".rstrip("_")
    run_dir = root / dirname
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir


def write_json_artifact(path: Path, payload: dict[str, Any] | list[Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2, default=str), encoding="utf-8")
    return path


def write_markdown_artifact(path: Path, content: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path
