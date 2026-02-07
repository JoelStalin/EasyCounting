"""Smoke tests for platform health endpoints."""
from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


def _build_client() -> AsyncClient:
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


@pytest.mark.asyncio
async def test_livez_endpoint() -> None:
    async with _build_client() as client:
        response = await client.get("/livez")
    assert response.status_code == 200
    assert response.json()["status"] == "alive"


@pytest.mark.asyncio
async def test_metrics_endpoint_exposes_prometheus_format() -> None:
    async with _build_client() as client:
        await client.get("/livez")
        response = await client.get("/metrics")
    assert response.status_code == 200
    assert "http_requests_total" in response.text
