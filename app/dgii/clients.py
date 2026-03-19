"""Compatibility wrapper for the unified DGII client."""
from __future__ import annotations

from typing import Any, Dict

from app.dgii.client import DGIIClient as _UnifiedClient


class DGIIClient(_UnifiedClient):
    """Backwards-compatible wrapper for legacy imports."""

    async def send_ecf(self, xml_bytes: bytes, token: str) -> Dict[str, Any]:
        return await super().send_ecf(xml_bytes, token=token)

    async def send_rfce(self, xml_bytes: bytes, token: str) -> Dict[str, Any]:
        return await super().send_rfce(xml_bytes, token=token)

    async def send_anecf(self, xml_bytes: bytes, token: str) -> Dict[str, Any]:
        return await super().send_anecf(xml_bytes, token=token)

    async def send_acecf(self, xml_bytes: bytes, token: str) -> Dict[str, Any]:
        return await super().send_acecf(xml_bytes, token=token)

    async def send_arecf(self, xml_bytes: bytes, token: str) -> Dict[str, Any]:
        return await super().send_arecf(xml_bytes, token=token)
