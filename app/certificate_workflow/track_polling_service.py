from __future__ import annotations

from app.certificate_workflow.models import WorkflowStatus
from app.certificate_workflow.persistence import CertificateWorkflowRepository
from app.dgii.client import DGIIClient
from app.infra.settings import settings
from app.shared.database import session_scope


def _extract_first(payload: dict, keys: list[str], default: str | None = None) -> str | None:
    for key in keys:
        if key in payload and payload[key] is not None:
            return str(payload[key])
    return default


def _extract_track_id(repo: CertificateWorkflowRepository, case_id: str) -> str | None:
    events = repo.list_events(case_id)
    for event in reversed(events):
        payload = event.event_payload or {}
        track_id = payload.get("track_id") or payload.get("trackId") or payload.get("track")
        if track_id:
            return str(track_id)
    return None


def _normalize_status(raw: str | None) -> str:
    value = (raw or "").strip().upper().replace(" ", "_")
    return value or "DESCONOCIDO"


def _is_terminal(status_value: str) -> bool:
    return status_value in {"ACEPTADO", "RECHAZADO", "ACEPTADO_CONDICIONAL"}


async def process_ready_cases_track_poll(*, limit: int = 50, live: bool = False) -> int:
    processed = 0
    with session_scope() as session:
        repo = CertificateWorkflowRepository(session)
        rows = repo.list_requests_by_status([WorkflowStatus.READY_FOR_DGII], limit=limit)
        for row in rows:
            track_id = _extract_track_id(repo, row.case_id)
            if not track_id:
                continue

            dgii_status = "EN_PROCESO"
            detail = "Auto poll simulado"
            mode = "simulated"

            if live:
                mode = "live"
                try:
                    async with DGIIClient() as client:
                        result = await client.get_status(track_id)
                        dgii_status = _normalize_status(
                            _extract_first(result, ["estado", "status", "respuesta"], "DESCONOCIDO")
                        )
                        detail = _extract_first(result, ["descripcion", "detalle", "message"], None) or detail
                except Exception as exc:  # noqa: BLE001
                    repo.append_event(
                        request_row=row,
                        event_type="DGII_TRACK_AUTOPOLL_FAILED",
                        payload={"track_id": track_id, "error": str(exc), "mode": mode},
                    )
                    continue

            repo.append_event(
                request_row=row,
                event_type="DGII_TRACK_AUTOPOLL_OK",
                payload={
                    "track_id": track_id,
                    "dgii_status": dgii_status,
                    "detail": detail,
                    "mode": mode,
                },
            )
            if _is_terminal(dgii_status) and dgii_status == "ACEPTADO":
                repo.transition_status(
                    row.case_id,
                    target_status=WorkflowStatus.IN_PRODUCTION_USE,
                    note="Auto track polling accepted",
                )
            processed += 1
    return processed


async def process_ready_cases_track_poll_from_settings() -> int:
    return await process_ready_cases_track_poll(
        limit=settings.certificate_workflow_track_poll_limit,
        live=settings.certificate_workflow_track_poll_live,
    )
