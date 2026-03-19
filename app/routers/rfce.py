"""RFCE submission endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.config import settings
from app.core.logging import bind_request_context
from app.dgii.client import DGIIClient
from app.dgii.schemas import RFCEPayload, RFCESubmissionResponse
from app.dgii.signing import sign_ecf
from app.dgii.validation import validate_xml
from app.routers.dependencies import BearerToken, DGIIClientDep, bind_request_headers

router = APIRouter(prefix="/dgii/rfce", tags=["DGII RFCE"])


@router.post("/resumen", response_model=RFCESubmissionResponse, status_code=status.HTTP_202_ACCEPTED)
async def enviar_rfce(
    payload: RFCEPayload,
    token: str = BearerToken,
    client: DGIIClient = DGIIClientDep,
    _trace = Depends(bind_request_headers),
) -> RFCESubmissionResponse:
    document = payload.to_model()
    xml = document.to_xml_bytes()
    validate_xml(xml, "RFCE.xsd")
    signed_xml = sign_ecf(xml, str(settings.dgii_cert_p12_path), settings.dgii_cert_p12_password)
    bind_request_context(encf=document.encf, tipo_ecf="RFCE")
    result = await client.send_rfce(signed_xml, token)
    return _build_rfce_response(result)


def _build_rfce_response(payload: dict) -> RFCESubmissionResponse:
    estado = payload.get("estado") or payload.get("status")
    codigo = payload.get("codigo") or payload.get("code")
    mensajes = payload.get("mensajes")
    if isinstance(mensajes, str):
        mensajes = [mensajes]
    if not estado or not codigo:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Respuesta RFCE incompleta")
    return RFCESubmissionResponse(codigo=codigo, estado=estado, mensajes=mensajes, encf=payload.get("encf"))

