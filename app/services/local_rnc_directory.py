"""Directorio RNC local para integracion Odoo sin dependencias externas."""
from __future__ import annotations

import json
from typing import Any

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.infra.settings import settings
from app.models.tenant import Tenant


def _digits(value: str) -> str:
    return "".join(char for char in value if char.isdigit())


def _normalize_name(value: str) -> str:
    return " ".join(value.upper().split())


def _record_from_tenant(tenant: Tenant) -> dict[str, Any]:
    rnc = _digits(tenant.rnc)
    return {
        "rnc": rnc,
        "vat": rnc,
        "name": tenant.name,
        "label": f"{rnc} - {tenant.name}",
        "commercial_name": tenant.name,
        "status": "ACTIVO",
        "category": "TENANT",
        "comment": "Registro interno sincronizado desde tenants.",
        "company_type": "company" if len(rnc) == 9 else "person",
        "is_company": len(rnc) == 9,
        "source": "tenant",
    }


def _record_from_catalog(entry: dict[str, Any]) -> dict[str, Any]:
    rnc = _digits(str(entry.get("rnc", "")))
    name = str(entry.get("name", "")).strip()
    commercial_name = str(entry.get("commercial_name", name)).strip() or name
    status = str(entry.get("status", "ACTIVO")).strip() or "ACTIVO"
    category = str(entry.get("category", "LOCAL")).strip() or "LOCAL"
    comment = str(
        entry.get(
            "comment",
            f"Directorio local {category.lower()} - estado: {status}.",
        )
    ).strip()
    return {
        "rnc": rnc,
        "vat": rnc,
        "name": name,
        "label": f"{rnc} - {name}",
        "commercial_name": commercial_name,
        "status": status,
        "category": category,
        "comment": comment,
        "company_type": str(entry.get("company_type", "company" if len(rnc) == 9 else "person")).strip(),
        "is_company": bool(entry.get("is_company", len(rnc) == 9)),
        "source": str(entry.get("source", "catalog")).strip() or "catalog",
    }


class LocalRncDirectoryService:
    """Busqueda local combinando tenants y un catalogo JSON versionado en el repo."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def _load_catalog(self) -> list[dict[str, Any]]:
        path = settings.odoo_rnc_catalog_path
        if not path.exists():
            return []
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return []
        if not isinstance(data, list):
            return []
        records: list[dict[str, Any]] = []
        for entry in data:
            if not isinstance(entry, dict):
                continue
            record = _record_from_catalog(entry)
            if record["rnc"] and record["name"]:
                records.append(record)
        return records

    def _load_tenants(self) -> list[dict[str, Any]]:
        try:
            tenants = self.db.scalars(select(Tenant).order_by(Tenant.name.asc())).all()
        except SQLAlchemyError:
            return []
        return [_record_from_tenant(tenant) for tenant in tenants if tenant.rnc and tenant.name]

    def _merged_records(self) -> list[dict[str, Any]]:
        records: list[dict[str, Any]] = []
        seen: set[str] = set()
        for record in [*self._load_tenants(), *self._load_catalog()]:
            if record["rnc"] in seen:
                continue
            seen.add(record["rnc"])
            records.append(record)
        return records

    def search(self, term: str, limit: int = 20) -> list[dict[str, Any]]:
        cleaned = term.strip()
        if not cleaned:
            return []

        digits = _digits(cleaned)
        normalized = _normalize_name(cleaned)
        ordered: list[dict[str, Any]] = []

        for record in self._merged_records():
            record_rnc = record["rnc"]
            record_name = _normalize_name(record["name"])
            if digits and record_rnc == digits:
                ordered.append(record)
                continue
            if digits and digits in record_rnc:
                ordered.append(record)
                continue
            if normalized and normalized in record_name:
                ordered.append(record)

        results: list[dict[str, Any]] = []
        seen: set[str] = set()
        for record in ordered:
            if record["rnc"] in seen:
                continue
            seen.add(record["rnc"])
            results.append(record)
            if len(results) >= limit:
                break
        return results

    def lookup(self, fiscal_id: str) -> dict[str, Any] | None:
        digits = _digits(fiscal_id)
        if len(digits) not in {9, 11}:
            return None
        for record in self._merged_records():
            if record["rnc"] == digits:
                return record
        return None
