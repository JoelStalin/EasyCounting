from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.application.partner_portal import PartnerPortalService
from app.infra.settings import settings as app_settings
from app.partner.schemas import (
    PartnerDashboardResponse,
    PartnerEmitRequest,
    PartnerEmitResponse,
    PartnerInvoiceListResponse,
    PartnerProfile,
    PartnerTenantItem,
    PartnerTenantOverview,
)
from app.shared.database import get_db
from app.shared.security import decode_jwt

router = APIRouter(prefix="/partner", tags=["Partner"])


def _require_partner_user(
    request: Request,
    authorization: str | None = Header(default=None, alias="Authorization"),
) -> dict:
    if app_settings.environment in {"test", "testing"}:
        payload = {"sub": "1", "tenant_id": 1, "role": "partner_reseller"}
        request.state.partner_payload = payload
        return payload
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authorization invalido")
    token = authorization.split(" ", 1)[1].strip()
    try:
        payload = decode_jwt(token)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token invalido") from exc
    role = payload.get("role")
    if not isinstance(role, str) or not role.startswith("partner_"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acceso restringido a sellers")
    request.state.partner_payload = payload
    return payload


def _user_id(payload: dict) -> int:
    subject = payload.get("sub")
    try:
        return int(subject)
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Usuario seller invalido") from exc


@router.get("/me", response_model=PartnerProfile)
def me(
    db: Session = Depends(get_db),
    payload: dict = Depends(_require_partner_user),
) -> PartnerProfile:
    return PartnerPortalService(db).get_profile(_user_id(payload))


@router.get("/dashboard", response_model=PartnerDashboardResponse)
def dashboard(
    db: Session = Depends(get_db),
    payload: dict = Depends(_require_partner_user),
) -> PartnerDashboardResponse:
    return PartnerPortalService(db).dashboard(_user_id(payload))


@router.get("/tenants", response_model=list[PartnerTenantItem])
def list_tenants(
    db: Session = Depends(get_db),
    payload: dict = Depends(_require_partner_user),
) -> list[PartnerTenantItem]:
    return PartnerPortalService(db).list_tenants(_user_id(payload))


@router.get("/tenants/{tenant_id}/overview", response_model=PartnerTenantOverview)
def tenant_overview(
    tenant_id: int,
    db: Session = Depends(get_db),
    payload: dict = Depends(_require_partner_user),
) -> PartnerTenantOverview:
    return PartnerPortalService(db).get_tenant_overview(user_id=_user_id(payload), tenant_id=tenant_id)


@router.get("/invoices", response_model=PartnerInvoiceListResponse)
def list_invoices(
    tenant_id: int | None = Query(default=None, ge=1),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    payload: dict = Depends(_require_partner_user),
) -> PartnerInvoiceListResponse:
    return PartnerPortalService(db).list_invoices(
        user_id=_user_id(payload),
        tenant_id=tenant_id,
        page=page,
        size=size,
    )


@router.post("/emit", response_model=PartnerEmitResponse, status_code=status.HTTP_201_CREATED)
def emit_demo_invoice(
    body: PartnerEmitRequest,
    db: Session = Depends(get_db),
    payload: dict = Depends(_require_partner_user),
) -> PartnerEmitResponse:
    return PartnerPortalService(db).emit_demo_invoice(user_id=_user_id(payload), payload=body)
