"""Recepción de e-CF y consulta de estado."""
from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.application.ecf_submission import build_status_response, submit_ecf
from app.billing.services import BillingService, get_billing_service
from app.dgii.client import DGIIClient
from app.dgii.jobs import dispatcher
from app.dgii.schemas import ECFSubmission, StatusResponse, SubmissionResponse
from app.routers.dependencies import BearerToken, DGIIClientDep, bind_request_headers
from app.shared.database import get_db

router = APIRouter(prefix="/dgii/recepcion", tags=["DGII Recepción"])


@router.post("/ecf", response_model=SubmissionResponse, status_code=status.HTTP_202_ACCEPTED)
async def enviar_ecf(
    payload: ECFSubmission,
    token: str = BearerToken,
    client: DGIIClient = DGIIClientDep,
    billing_service: BillingService = Depends(get_billing_service),
    db: Session = Depends(get_db),
    _trace = Depends(bind_request_headers),
) -> SubmissionResponse:
    return await submit_ecf(
        payload=payload,
        token=token,
        client=client,
        billing_service=billing_service,
        db=db,
        dispatcher=dispatcher,
    )


@router.get("/status/{track_id}", response_model=StatusResponse)
async def estado_recepcion(
    track_id: str,
    token: str = BearerToken,
    client: DGIIClient = DGIIClientDep,
    _trace = Depends(bind_request_headers),
) -> StatusResponse:
    result = await client.get_status(track_id, token)
    return build_status_response(track_id, result)

