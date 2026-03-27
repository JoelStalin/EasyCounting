from __future__ import annotations

from app.dgii.client import DGIIClient


class DgiiRecepcionService:
    def __init__(self, client: DGIIClient):
        self.client = client

    async def submit_signed_ecf(self, xml_signed: bytes, idempotency_key: str, token: str | None = None) -> dict:
        return await self.client.send_ecf(xml_signed, token=token, idempotency_key=idempotency_key)
