"""Structured exports and audit trace generation."""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
import csv
import json
from pathlib import Path
from typing import Any

from app.dgii_portal_automation.errors import DGIIConfigurationError, DGIIReportingError


def build_json_report(payload: Any, output_path: str | Path, *, indent: int = 2) -> Path:
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", encoding="utf-8") as handle:
        json.dump(_serialize(payload), handle, ensure_ascii=False, indent=indent)
    return destination


def build_csv_report(rows: list[dict[str, Any]], output_path: str | Path, *, encoding: str = "utf-8") -> Path:
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    normalized_rows = [_serialize(row) for row in rows]
    fieldnames: list[str] = []
    for row in normalized_rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    with destination.open("w", encoding=encoding, newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames or ["value"])
        writer.writeheader()
        for row in normalized_rows:
            writer.writerow(row)
    return destination


def build_excel_report(rows: list[dict[str, Any]], output_path: str | Path, *, sheet_name: str = "DGII") -> Path:
    try:
        from openpyxl import Workbook
    except ImportError as exc:  # pragma: no cover - dependency guard
        raise DGIIConfigurationError("openpyxl no esta instalado. Instala openpyxl para exportar a Excel.") from exc

    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    normalized_rows = [_serialize(row) for row in rows]
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = sheet_name
    headers: list[str] = []
    for row in normalized_rows:
        for key in row:
            if key not in headers:
                headers.append(key)
    if not headers:
        headers = ["value"]
    sheet.append(headers)
    for row in normalized_rows:
        sheet.append([row.get(header, "") for header in headers])
    workbook.save(destination)
    return destination


def generate_audit_trace(runtime: Any, output_path: str | Path) -> Path:
    if runtime is None:
        raise DGIIReportingError("Se requiere un runtime para generar la traza de auditoria")
    payload = {
        "current_url": getattr(runtime, "current_url", None),
        "audit_events": [_serialize(item) for item in getattr(runtime, "audit_events", [])],
        "downloads": [_serialize(item) for item in getattr(runtime, "downloads", [])],
    }
    return build_json_report(payload, output_path)


def _serialize(value: Any) -> Any:
    if is_dataclass(value):
        return {key: _serialize(item) for key, item in asdict(value).items()}
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {str(key): _serialize(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_serialize(item) for item in value]
    if isinstance(value, tuple):
        return [_serialize(item) for item in value]
    if hasattr(value, "isoformat"):
        try:
            return value.isoformat()
        except Exception:
            return str(value)
    return value
