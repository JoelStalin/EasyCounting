from __future__ import annotations

from app.dgii.client import DGIIClient


class DgiiConsultaService:
    def __init__(self, client: DGIIClient):
        self.client = client

    async def query_trackid(self, track_id: str, token: str | None = None) -> dict:
        return await self.client.get_status(track_id, token=token)
