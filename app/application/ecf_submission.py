"""Application service for DGII e-CF submissions."""
from __future__ import annotations

from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.billing.services import BillingError, BillingService
from app.core.logging import bind_request_context
from app.dgii.client import DGIIClient
from app.dgii.jobs import DGIIJobDispatcher
from app.dgii.schemas import ECFSubmission, StatusResponse, SubmissionResponse
from app.dgii.signing import sign_ecf
from app.dgii.validation import validate_xml
from app.infra.settings import settings
from app.models.invoice import Invoice
from app.shared.storage import storage
from app.models.tenant import Tenant


def _extract_first(payload: dict, keys: list[str], default: str | None = None) -> str | None:
    for key in keys:
        if key in payload and payload[key] is not None:
            return payload[key]
    return default


def build_submission_response(payload: dict) -> SubmissionResponse:
    track_id = _extract_first(payload, ["track_id", "trackId", "track"])
    status_value = _extract_first(payload, ["status", "estado", "respuesta"])
    mensajes = payload.get("mensajes") or payload.get("mensajes_detalle")
    if isinstance(mensajes, str):
        mensajes = [mensajes]
    if not track_id or not status_value:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Respuesta DGII incompleta")
    return SubmissionResponse(track_id=track_id, status=status_value, messages=mensajes)


def build_status_response(track_id: str, payload: dict) -> StatusResponse:
    estado = _extract_first(payload, ["estado", "status"])
    descripcion = _extract_first(payload, ["descripcion", "detalle", "message"], default=None)
    if not estado:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Estado no disponible")
    return StatusResponse(track_id=track_id, estado=estado, descripcion=descripcion)


async def submit_ecf(
    *,
    payload: ECFSubmission,
    token: str,
    client: DGIIClient,
    billing_service: BillingService,
    db: Session,
    dispatcher: DGIIJobDispatcher,
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
    result = await client.send_ecf(signed_xml, token=token)
    response = build_submission_response(result)

    tenant = db.scalar(select(Tenant).where(Tenant.rnc == payload.rnc_emisor))
    if not tenant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant no encontrado para el RNC emisor")

    xml_relative_path = f"xml/{payload.encf}.xml"
    try:
        storage.store_bytes(xml_relative_path, signed_xml)
    except FileExistsError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="XML ya almacenado") from exc
    xml_hash = storage.compute_hash(xml_relative_path)
    invoice = Invoice(
        tenant_id=tenant.id,
        encf=payload.encf,
        tipo_ecf=payload.tipo_ecf[:3],
        rnc_receptor=payload.rnc_receptor,
        xml_path=xml_relative_path,
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
