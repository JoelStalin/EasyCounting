"""Rutas internas para automatización local controlada."""
from __future__ import annotations

import base64
import binascii
import ipaddress

from fastapi import APIRouter, Depends, File, Form, Header, HTTPException, Request, UploadFile, status
from pydantic import BaseModel, Field
from pydantic.config import ConfigDict
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.application.certificates import TenantCertificateService
from app.infra.settings import settings
from app.models.tenant import Tenant
from app.portal_client.schemas import TenantCertificateSignResponse, TenantCertificateUploadResponse
from app.shared.database import get_db

router = APIRouter(prefix="/internal", tags=["internal"], include_in_schema=False)


class InternalCertificateSignRequest(BaseModel):
    xml: str = Field(..., description="Documento XML sin firmar en base64")
    tenant_id: int | None = Field(default=None, alias="tenantId")
    tenant_rnc: str | None = Field(default=None, alias="tenantRnc")
    reference_uri: str = Field(default="", alias="referenceUri")
    allow_env_fallback: bool = Field(default=True, alias="allowEnvFallback")

    model_config = ConfigDict(populate_by_name=True)


def _is_local_internal_host(client_host: str | None) -> bool:
    if client_host in {"localhost", "testclient", "host.docker.internal"}:
        return True
    if not client_host:
        return False
    try:
        ip = ipaddress.ip_address(client_host)
    except ValueError:
        return False
    return ip.is_loopback or ip.is_private or ip.is_link_local


def _resolve_internal_tenant_id(db: Session, tenant_id: int | None, tenant_rnc: str | None) -> int:
    if tenant_id is not None:
        resolved_id = db.scalar(select(Tenant.id).where(Tenant.id == tenant_id).limit(1))
        if resolved_id is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant no encontrado")
        return int(resolved_id)
    normalized_rnc = (tenant_rnc or "").strip()
    if normalized_rnc:
        resolved_id = db.scalar(select(Tenant.id).where(Tenant.rnc == normalized_rnc).limit(1))
        if resolved_id is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant no encontrado para el RNC indicado")
        return int(resolved_id)
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="tenant_id o tenant_rnc son obligatorios")


def _require_internal_secret(
    request: Request,
    x_internal_secret: str | None = Header(default=None, alias="X-Internal-Secret"),
) -> None:
    if x_internal_secret != settings.hmac_service_secret:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Internal secret invalido")
    client_host = request.client.host if request.client else None
    if not _is_local_internal_host(client_host):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acceso interno restringido a loopback local")


@router.post("/certificates/sign-xml", response_model=TenantCertificateSignResponse)
def sign_xml_internal(
    body: InternalCertificateSignRequest,
    db: Session = Depends(get_db),
    _internal: None = Depends(_require_internal_secret),
) -> TenantCertificateSignResponse:
    try:
        xml_bytes = base64.b64decode(body.xml)
    except (ValueError, binascii.Error) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="XML base64 invalido") from exc
    signed_xml, runtime = TenantCertificateService(db).sign_xml(
        xml_bytes,
        tenant_id=body.tenant_id,
        tenant_rnc=body.tenant_rnc,
        allow_env_fallback=body.allow_env_fallback,
        reference_uri=body.reference_uri,
    )
    return TenantCertificateSignResponse(
        xmlSigned=base64.b64encode(signed_xml).decode("utf-8"),
        certificateId=runtime.certificate_id,
        certificateAlias=runtime.alias,
        certificateSubject=runtime.subject,
        source=runtime.source,
    )


@router.post(
    "/certificates/register",
    response_model=TenantCertificateUploadResponse,
    status_code=status.HTTP_201_CREATED,
)
def register_certificate_internal(
    tenant_id: int | None = Form(default=None),
    tenant_rnc: str | None = Form(default=None),
    alias: str = Form(...),
    password: str = Form(...),
    activate: bool = Form(default=True),
    certificate: UploadFile = File(...),
    db: Session = Depends(get_db),
    _internal: None = Depends(_require_internal_secret),
) -> TenantCertificateUploadResponse:
    target_tenant_id = _resolve_internal_tenant_id(db, tenant_id, tenant_rnc)
    bundle = certificate.file.read()
    return TenantCertificateService(db).upload_certificate(
        tenant_id=target_tenant_id,
        alias=alias,
        password=password,
        p12_bytes=bundle,
        filename=certificate.filename,
        activate=activate,
        actor="internal_service",
    )
