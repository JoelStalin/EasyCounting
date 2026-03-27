from __future__ import annotations

from app.dgii.application.dgii_recepcion_service import DgiiRecepcionService


class SubmitEcfUseCase:
    def __init__(self, recepcion_service: DgiiRecepcionService):
        self.recepcion_service = recepcion_service

    async def execute(self, xml_signed: bytes, idempotency_key: str, token: str | None = None) -> dict:
        return await self.recepcion_service.submit_signed_ecf(
            xml_signed=xml_signed,
            idempotency_key=idempotency_key,
            token=token,
        )
