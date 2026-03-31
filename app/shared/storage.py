"""Abstracciones de almacenamiento WORM y manejo de archivos."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict

from app.shared.settings import settings


def _json_default(obj: Any) -> Any:
    """Encoder por defecto para tipos no serializables por json estándar."""
    if isinstance(obj, Decimal):
        return float(obj)
    if isinstance(obj, (datetime,)):
        return obj.isoformat()
    return str(obj)


class LocalStorage:
    """Implementación simple de almacenamiento inmutable local."""

    def __init__(self, base_path: Path | None = None) -> None:
        self.base_path = base_path or settings.storage_base_path
        self.base_path.mkdir(parents=True, exist_ok=True)

    def store_bytes(self, relative_path: str, data: bytes) -> Path:
        """Guarda datos como archivo WORM calculando hash SHA-512."""

        target = self.base_path / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            raise FileExistsError(f"El archivo {target} ya existe (WORM)")
        target.write_bytes(data)
        return target

    def store_json(self, relative_path: str, payload: Dict[str, Any]) -> Path:
        """Serializa un JSON y lo guarda en disco."""

        serialized = json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            default=_json_default,
        ).encode("utf-8")
        return self.store_bytes(relative_path, serialized)

    def compute_hash(self, relative_path: str) -> str:
        """Calcula el hash SHA-512 encadenado."""

        target = self.base_path / relative_path
        digest = hashlib.sha512(target.read_bytes()).hexdigest()
        metadata_path = target.with_suffix(target.suffix + ".meta.json")
        metadata = {
            "path": str(target),
            "hash": digest,
            "computed_at": datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + "Z",
        }
        metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
        return digest

    def resolve_path(self, relative_path: str) -> Path:
        """Resolve a relative storage path to an absolute filesystem path."""

        return self.base_path / relative_path


storage = LocalStorage()
