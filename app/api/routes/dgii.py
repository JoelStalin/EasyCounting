"""DGII document submission endpoints."""
from __future__ import annotations

import uuid
from fastapi import APIRouter, Depends, HTTPException

from app.domain.models.acecf import ACECF
from app.domain.models.arecf import ARECF
from app.domain.models.ecf import ECF
from app.domain.models.rfce import RFCE
from app.security.xml import validate_with_xsd
from app.services.dgii_client import DGIIClient, get_dgii_client

router = APIRouter()


@router.post("/auth/token")
async def compat_auth_token() -> dict[str, str]:
    return {"access_token": f"local-{uuid.uuid4().hex}"}


@router.post("/recepcion/ecf", status_code=202)
async def compat_recepcion_ecf() -> dict[str, str]:
    return {"trackId": f"LOCAL-{uuid.uuid4().hex[:12].upper()}", "estado": "EN_PROCESO"}


@router.get("/recepcion/status/{track_id}")
async def compat_recepcion_status(track_id: str) -> dict[str, str]:
    return {"trackId": track_id, "estado": "ACEPTADO", "descripcion": "Procesado"}


@router.post("/ecf/send")
async def send_ecf(payload: ECF, client: DGIIClient = Depends(get_dgii_client)) -> dict[str, str]:
    xml_bytes = payload.to_xml()
    validate_with_xsd(xml_bytes, "xsd/ecf.xsd")
    return await client.send_document(xml_bytes, document_type="ecf")


@router.post("/rfce/send")
async def send_rfce(payload: RFCE, client: DGIIClient = Depends(get_dgii_client)) -> dict[str, str]:
    xml_bytes = payload.to_xml()
    validate_with_xsd(xml_bytes, "xsd/rfce.xsd")
    return await client.send_document(xml_bytes, document_type="rfce")


@router.post("/acecf/send")
async def send_acecf(payload: ACECF, client: DGIIClient = Depends(get_dgii_client)) -> dict[str, str]:
    xml_bytes = payload.to_xml()
    validate_with_xsd(xml_bytes, "xsd/acecf.xsd")
    return await client.send_document(xml_bytes, document_type="acecf")


@router.post("/arecf/send")
async def send_arecf(payload: ARECF, client: DGIIClient = Depends(get_dgii_client)) -> dict[str, str]:
    xml_bytes = payload.to_xml()
    validate_with_xsd(xml_bytes, "xsd/arecf.xsd")
    return await client.send_document(xml_bytes, document_type="arecf")


@router.get("/status/{track_id}")
async def get_status(track_id: str, client: DGIIClient = Depends(get_dgii_client)) -> dict[str, str]:
    response = await client.get_status(track_id)
    if not response:
        raise HTTPException(status_code=404, detail="Track ID not found")
    return response
