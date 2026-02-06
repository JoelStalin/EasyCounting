"""Rutas de firmado."""
from __future__ import annotations

from fastapi import APIRouter

from app.sign.schemas import SignXMLRequest, SignXMLResponse
from app.sign.service import SignService

router = APIRouter()
service = SignService()


@router.post("/{tenant}/sign/xml", response_model=SignXMLResponse)
async def sign_xml(tenant: str, payload: SignXMLRequest) -> SignXMLResponse:
    """Firma un XML utilizando el certificado del tenant."""

    return service.sign(payload)


@router.post("/sign/xml", response_model=SignXMLResponse)
async def sign_xml_default(payload: SignXMLRequest) -> SignXMLResponse:
    return service.sign(payload)
