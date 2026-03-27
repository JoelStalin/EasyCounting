from __future__ import annotations

from app.dgii.application.dgii_consulta_service import DgiiConsultaService


class PollTrackIdUseCase:
    def __init__(self, consulta_service: DgiiConsultaService):
        self.consulta_service = consulta_service

    async def execute(self, track_id: str, token: str | None = None) -> dict:
        return await self.consulta_service.query_trackid(track_id, token=token)
