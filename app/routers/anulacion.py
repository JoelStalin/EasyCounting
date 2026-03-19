"""ANECF submission endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends, status

from app.core.config import settings
from app.core.logging import bind_request_context
from app.dgii.client import DGIIClient
from app.dgii.schemas import ANECFPayload, SubmissionResponse
from app.dgii.signing import sign_ecf
from app.dgii.validation import validate_xml
from app.routers.dependencies import BearerToken, DGIIClientDep, bind_request_headers
from app.application.ecf_submission import build_submission_response

router = APIRouter(prefix="/dgii/anulacion", tags=["DGII ANECF"])


@router.post("/anecf", response_model=SubmissionResponse, status_code=status.HTTP_202_ACCEPTED)
async def enviar_anecf(
    payload: ANECFPayload,
    token: str = BearerToken,
    client: DGIIClient = DGIIClientDep,
    _trace = Depends(bind_request_headers),
) -> SubmissionResponse:
    document = payload.to_model()
    xml = document.to_xml_bytes()
    validate_xml(xml, "ANECF.xsd")
    signed_xml = sign_ecf(xml, str(settings.dgii_cert_p12_path), settings.dgii_cert_p12_password)
    bind_request_context(encf=document.encf, tipo_ecf="ANECF")
    result = await client.send_anecf(signed_xml, token)
    return build_submission_response(result)

