from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.application.tenant_api import READ_SCOPE, WRITE_SCOPE, TenantApiService
from app.shared.database import get_db
from app.tenant_api.schemas import (
    TenantApiInvoiceCreateRequest,
    TenantApiInvoiceCreateResponse,
    TenantApiInvoiceDetailResponse,
    TenantApiInvoiceListResponse,
)

router = APIRouter(prefix="/tenant-api", tags=["Tenant API"])


def _require_tenant_api_token(authorization: str | None, db: Session, *, required_scope: str):
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authorization invalido")
    raw_token = authorization.split(" ", 1)[1].strip()
    return TenantApiService(db).authenticate_token(raw_token, required_scope=required_scope)


def _authorization_header(authorization: str | None = Header(default=None, alias="Authorization")) -> str | None:
    return authorization


def _read_token(
    authorization: str | None = Depends(_authorization_header),
    db: Session = Depends(get_db),
):
    return _require_tenant_api_token(authorization, db, required_scope=READ_SCOPE)


def _write_token(
    authorization: str | None = Depends(_authorization_header),
    db: Session = Depends(get_db),
):
    return _require_tenant_api_token(authorization, db, required_scope=WRITE_SCOPE)


@router.get("/invoices", response_model=TenantApiInvoiceListResponse)
def list_invoices(
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    encf: str | None = Query(default=None, max_length=20),
    estado_dgii: str | None = Query(default=None, max_length=40),
    db: Session = Depends(get_db),
    token=Depends(_read_token),
) -> TenantApiInvoiceListResponse:
    return TenantApiService(db).list_invoices(
        tenant_id=token.tenant_id,
        page=page,
        size=size,
        encf=encf,
        estado_dgii=estado_dgii,
    )


@router.get("/invoices/{invoice_id}", response_model=TenantApiInvoiceDetailResponse)
def get_invoice(
    invoice_id: int,
    db: Session = Depends(get_db),
    token=Depends(_read_token),
) -> TenantApiInvoiceDetailResponse:
    return TenantApiService(db).get_invoice_detail(tenant_id=token.tenant_id, invoice_id=invoice_id)


@router.post("/invoices", response_model=TenantApiInvoiceCreateResponse, status_code=status.HTTP_201_CREATED)
def create_invoice(
    payload: TenantApiInvoiceCreateRequest,
    db: Session = Depends(get_db),
    token=Depends(_write_token),
) -> TenantApiInvoiceCreateResponse:
    return TenantApiService(db).create_invoice(tenant_id=token.tenant_id, payload=payload)
