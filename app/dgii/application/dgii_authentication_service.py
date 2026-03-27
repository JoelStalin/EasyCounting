from __future__ import annotations

from app.dgii.client import DGIIClient


class DgiiAuthenticationService:
    """Encapsulate DGII seed and token flow with client caching semantics."""

    def __init__(self, client: DGIIClient):
        self.client = client

    async def get_token(self, force_refresh: bool = False) -> dict[str, str]:
        token = await self.client.bearer(force_refresh=force_refresh)
        return {"access_token": token}
