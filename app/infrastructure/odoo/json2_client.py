"""Minimal Odoo 19 JSON-2 client."""
from __future__ import annotations

from typing import Any

import httpx


class OdooJSON2Error(RuntimeError):
    """Raised when the Odoo JSON-2 API returns an invalid response."""


class OdooJSON2Client:
    """Thin async wrapper over Odoo 19 `/json/2` endpoints."""

    def __init__(
        self,
        *,
        base_url: str,
        api_key: str,
        database: str | None = None,
        timeout: float = 20.0,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        sanitized = base_url.rstrip("/")
        self.base_url = sanitized if sanitized.endswith("/json/2") else f"{sanitized}/json/2"
        self.api_key = api_key
        self.database = database
        self._own_client = client is None
        self._client = client or httpx.AsyncClient(timeout=timeout)

    async def __aenter__(self) -> "OdooJSON2Client":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.close()

    async def close(self) -> None:
        if self._own_client:
            await self._client.aclose()

    async def call(self, model: str, method: str, payload: dict[str, Any] | None = None) -> Any:
        body = payload or {}
        headers = {
            "Authorization": f"bearer {self.api_key}",
            "Content-Type": "application/json",
            "User-Agent": "dgii-encf/odoo-json2",
        }
        if self.database:
            headers["X-Odoo-Database"] = self.database
        response = await self._client.post(f"{self.base_url}/{model}/{method}", headers=headers, json=body)
        response.raise_for_status()
        try:
            return response.json()
        except ValueError as exc:
            raise OdooJSON2Error("Odoo JSON-2 devolvio una respuesta no JSON") from exc

    async def search_read(
        self,
        model: str,
        *,
        domain: list[list[Any]] | list[tuple[Any, ...]],
        fields: list[str],
        limit: int = 1,
        context: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        return await self.call(
            model,
            "search_read",
            {
                "domain": domain,
                "fields": fields,
                "limit": limit,
                "context": context or {},
            },
        )

    async def create(self, model: str, values: dict[str, Any], *, context: dict[str, Any] | None = None) -> Any:
        return await self.call(model, "create", {"vals_list": [values], "context": context or {}})

    async def write(self, model: str, ids: list[int], values: dict[str, Any], *, context: dict[str, Any] | None = None) -> Any:
        return await self.call(model, "write", {"ids": ids, "vals": values, "context": context or {}})

    async def read(self, model: str, ids: list[int], *, fields: list[str], context: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        return await self.call(model, "read", {"ids": ids, "fields": fields, "context": context or {}})

    async def action(self, model: str, method: str, ids: list[int], *, context: dict[str, Any] | None = None) -> Any:
        return await self.call(model, method, {"ids": ids, "context": context or {}})

