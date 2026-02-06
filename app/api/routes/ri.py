"""Placeholder for RI rendering."""
from __future__ import annotations

from fastapi import APIRouter

router = APIRouter()


@router.get("/render")
async def render_ri() -> dict[str, str]:
    return {"detail": "RI rendering pending"}


@router.post("/render")
async def render_ri_post() -> dict[str, str]:
    return {"html": "<html></html>", "qr_base64": ""}
