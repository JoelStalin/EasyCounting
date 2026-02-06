"""Recepción de e-CF y consulta de estado."""
from __future__ import annotations

import hashlib
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.billing.services import BillingError, BillingService, get_billing_service
from app.core.config import settings
from app.core.logging import bind_request_context
from app.dgii.clients import DGIIClient
from app.dgii.jobs import dispatcher
from app.dgii.schemas import ECFSubmission, StatusResponse, SubmissionResponse
from app.dgii.signing import sign_ecf
from app.dgii.validation import validate_xml
from app.models.invoice import Invoice
from app.models.tenant import Tenant
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
    try:
        billing_service.assert_ecf_allowed(
            rnc=payload.rnc_emisor,
            rnc_receptor=payload.rnc_receptor,
            monto_total=Decimal(str(payload.monto_total)),
            when=payload.fecha_emision,
        )
    except BillingError as exc:
        raise HTTPException(status_code=status.HTTP_402_PAYMENT_REQUIRED, detail=str(exc)) from exc

    document = payload.to_model()
    xml = document.to_xml_bytes()
    validate_xml(xml, "ECF.xsd")
    signed_xml = sign_ecf(xml, str(settings.dgii_cert_p12_path), settings.dgii_cert_p12_password)
    bind_request_context(tipo_ecf=document.tipo_ecf, encf=document.encf)
    result = await client.send_ecf(signed_xml, token)
    response = _build_submission_response(result)

    tenant = db.scalar(select(Tenant).where(Tenant.rnc == payload.rnc_emisor))
    if not tenant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant no encontrado para el RNC emisor")

    xml_hash = hashlib.sha256(signed_xml).hexdigest()
    invoice = Invoice(
        tenant_id=tenant.id,
        encf=payload.encf,
        tipo_ecf=payload.tipo_ecf[:3],
        rnc_receptor=payload.rnc_receptor,
        xml_path=f"xml/{payload.encf}.xml",
        xml_hash=xml_hash,
        estado_dgii=str(response.status),
        track_id=response.track_id,
        codigo_seguridad=None,
        total=float(payload.monto_total),
        fecha_emision=payload.fecha_emision,
    )
    db.add(invoice)
    db.flush()

    try:
        billing_service.record_usage_for_rnc(
            rnc=payload.rnc_emisor,
            ecf_type=payload.tipo_ecf,
            track_id=response.track_id,
            invoice_id=invoice.id,
        )
    except BillingError as exc:
        raise HTTPException(status_code=status.HTTP_402_PAYMENT_REQUIRED, detail=str(exc)) from exc

    await dispatcher.enqueue_status_check(response.track_id, token)
    return response


@router.get("/status/{track_id}", response_model=StatusResponse)
async def estado_recepcion(
    track_id: str,
    token: str = BearerToken,
    client: DGIIClient = DGIIClientDep,
    _trace = Depends(bind_request_headers),
) -> StatusResponse:
    result = await client.get_status(track_id, token)
    return _build_status_response(track_id, result)


def _build_submission_response(payload: dict) -> SubmissionResponse:
    track_id = _extract_first(payload, ["track_id", "trackId", "track"])
    status_value = _extract_first(payload, ["status", "estado", "respuesta"])
    mensajes = payload.get("mensajes") or payload.get("mensajes_detalle")
    if isinstance(mensajes, str):
        mensajes = [mensajes]
    if not track_id or not status_value:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Respuesta DGII incompleta")
    return SubmissionResponse(track_id=track_id, status=status_value, messages=mensajes)


def _build_status_response(track_id: str, payload: dict) -> StatusResponse:
    estado = _extract_first(payload, ["estado", "status"])
    descripcion = _extract_first(payload, ["descripcion", "detalle", "message"], default=None)
    if not estado:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Estado no disponible")
    return StatusResponse(track_id=track_id, estado=estado, descripcion=descripcion)


def _extract_first(payload: dict, keys: list[str], default: str | None = None) -> str | None:
    for key in keys:
        if key in payload and payload[key] is not None:
            return payload[key]
    return default
