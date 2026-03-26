"""Helpers to normalize Odoo accounting synchronization results."""
from __future__ import annotations

from typing import Any


def normalize_move_snapshot(payload: dict[str, Any] | None) -> dict[str, Any]:
    data = payload or {}
    return {
        "id": data.get("id"),
        "name": data.get("name"),
        "state": data.get("state"),
        "payment_state": data.get("payment_state"),
        "move_type": data.get("move_type"),
    }


def sync_state_from_snapshot(payload: dict[str, Any] | None) -> str:
    snapshot = normalize_move_snapshot(payload)
    if snapshot["id"] is None:
        return "FAILED"
    if snapshot["state"] == "posted":
        return "SYNCED_TO_ODOO"
    return "SYNCED_DRAFT"
