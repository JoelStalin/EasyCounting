"""Compatibility wrapper for legacy imports of DGII client."""
from __future__ import annotations

from app.dgii.client import DGIIClient


async def get_dgii_client() -> DGIIClient:
    return DGIIClient()
