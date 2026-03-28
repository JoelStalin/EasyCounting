"""Endpoints administrativos para contabilidad y configuración de empresas."""
from __future__ import annotations

from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, Response, status
from sqlalchemy.orm import Session

from app.application.admin_portal import AdminService
from app.admin.schemas import (
    AuditLogItem,
    BillingSummaryResponse,
    DashboardKpisResponse,
    InvoiceDetailResponse,
    InvoiceListResponse,
    LedgerEntryCreate,
    LedgerEntryItem,
    LedgerPaginatedResponse,
    LedgerSummaryResponse,
    PlanCreate,
    PlanResponse,
    PlanUpdate,
    TenantPlanAssignment,
    TenantPlanResponse,
    TenantSettingsPayload,
    TenantSettingsResponse,
    TenantCreate,
    TenantItem,
    TenantUpdate,
    PlatformAIProviderItem,
    PlatformAIProviderPayload,
    PlatformUserItem,
    TenantAIProviderItem,
    TenantAIProviderPayload,
    UserAIProviderItem,
    UserAIProviderPayload,
)
from app.infra.settings import settings as app_settings
from app.shared.database import get_db
from app.shared.security import decode_jwt


def _require_platform_user(
    request: Request,
    authorization: str | None = Header(default=None, alias="Authorization"),
) -> dict:
    if app_settings.environment in {"test", "testing"}:
        request.state.platform_payload = {}
        return {}
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authorization inválido")
    token = authorization.split(" ", 1)[1].strip()
    try:
        payload = decode_jwt(token)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido") from exc
    role = payload.get("role")
    if not isinstance(role, str) or not role.startswith("platform_"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acceso restringido a plataforma")
    request.state.platform_payload = payload
    return payload


router = APIRouter(prefix="/admin", tags=["Admin"], dependencies=[Depends(_require_platform_user)])


def _platform_payload(request: Request | None) -> dict:
    if request is None:
        return {}
    return getattr(request.state, "platform_payload", {})


def _service(db: Session, request: Request | None = None) -> AdminService:
    return AdminService(db, _platform_payload(request))


@router.get("/tenants", response_model=List[TenantItem])
def list_tenants(db: Session = Depends(get_db)) -> List[TenantItem]:
    return _service(db).list_tenants()


@router.post("/tenants", response_model=TenantItem, status_code=status.HTTP_201_CREATED)
def create_tenant(
    request: Request,
    payload: TenantCreate,
    db: Session = Depends(get_db),
) -> TenantItem:
    return _service(db, request).create_tenant(payload)


@router.get("/dashboard/kpis", response_model=DashboardKpisResponse)
def dashboard_kpis(
    month: str | None = Query(default=None, pattern=r"^\d{4}-\d{2}$"),
    db: Session = Depends(get_db),
) -> DashboardKpisResponse:
    return _service(db).dashboard_kpis(month)


@router.get("/invoices", response_model=InvoiceListResponse)
def list_invoices(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    tenant_id: int | None = Query(default=None, ge=1),
    estado_dgii: str | None = Query(default=None, max_length=30),
    tipo_ecf: str | None = Query(default=None, max_length=3),
    encf: str | None = Query(default=None, max_length=20),
    track_id: str | None = Query(default=None, max_length=64),
    date_from: datetime | None = Query(default=None),
    date_to: datetime | None = Query(default=None),
) -> InvoiceListResponse:
    return _service(db).list_invoices(
        page=page,
        size=size,
        tenant_id=tenant_id,
        estado_dgii=estado_dgii,
        tipo_ecf=tipo_ecf,
        encf=encf,
        track_id=track_id,
        date_from=date_from,
        date_to=date_to,
    )


@router.get("/invoices/{invoice_id}", response_model=InvoiceDetailResponse)
def get_invoice(invoice_id: int, db: Session = Depends(get_db)) -> InvoiceDetailResponse:
    return _service(db).get_invoice(invoice_id)


@router.get("/tenants/{tenant_id}", response_model=TenantItem)
def get_tenant(tenant_id: int, db: Session = Depends(get_db)) -> TenantItem:
    return _service(db).get_tenant(tenant_id)


@router.put("/tenants/{tenant_id}", response_model=TenantItem)
def update_tenant(
    request: Request,
    tenant_id: int,
    payload: TenantUpdate,
    db: Session = Depends(get_db),
) -> TenantItem:
    return _service(db, request).update_tenant(tenant_id, payload)


@router.get("/plans", response_model=List[PlanResponse])
def list_plans(db: Session = Depends(get_db)) -> List[PlanResponse]:
    return _service(db).list_plans()


@router.post("/plans", response_model=PlanResponse, status_code=status.HTTP_201_CREATED)
def create_plan(
    request: Request,
    payload: PlanCreate,
    db: Session = Depends(get_db),
) -> PlanResponse:
    return _service(db, request).create_plan(payload)


@router.put("/plans/{plan_id}", response_model=PlanResponse)
def update_plan(
    request: Request,
    plan_id: int,
    payload: PlanUpdate,
    db: Session = Depends(get_db),
) -> PlanResponse:
    return _service(db, request).update_plan(plan_id, payload)


@router.delete("/plans/{plan_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_plan(
    request: Request,
    plan_id: int,
    db: Session = Depends(get_db),
) -> Response:
    _service(db, request).delete_plan(plan_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/tenants/{tenant_id}/accounting/summary", response_model=LedgerSummaryResponse)
def get_accounting_summary(tenant_id: int, db: Session = Depends(get_db)) -> LedgerSummaryResponse:
    return _service(db).get_accounting_summary(tenant_id)


@router.get("/tenants/{tenant_id}/accounting/ledger", response_model=LedgerPaginatedResponse)
def list_ledger_entries(
    tenant_id: int,
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    contabilizado: bool | None = Query(None),
) -> LedgerPaginatedResponse:
    return _service(db).list_ledger_entries(
        tenant_id=tenant_id,
        page=page,
        size=size,
        contabilizado=contabilizado,
    )


@router.post("/tenants/{tenant_id}/accounting/ledger", response_model=LedgerEntryItem, status_code=status.HTTP_201_CREATED)
def create_ledger_entry(
    tenant_id: int,
    payload: LedgerEntryCreate,
    db: Session = Depends(get_db),
) -> LedgerEntryItem:
    return _service(db).create_ledger_entry(tenant_id, payload)


@router.get("/tenants/{tenant_id}/settings", response_model=TenantSettingsResponse)
def get_tenant_settings(tenant_id: int, db: Session = Depends(get_db)) -> TenantSettingsResponse:
    return _service(db).get_tenant_settings(tenant_id)


@router.put("/tenants/{tenant_id}/plan", response_model=TenantPlanResponse)
def assign_tenant_plan(
    request: Request,
    tenant_id: int,
    payload: TenantPlanAssignment,
    db: Session = Depends(get_db),
) -> TenantPlanResponse:
    return _service(db, request).assign_tenant_plan(tenant_id, payload)


@router.get("/tenants/{tenant_id}/plan", response_model=TenantPlanResponse)
def get_tenant_plan(tenant_id: int, db: Session = Depends(get_db)) -> TenantPlanResponse:
    return _service(db).get_tenant_plan(tenant_id)


@router.get("/billing/summary", response_model=BillingSummaryResponse)
def admin_billing_summary(
    month: str | None = Query(default=None, pattern=r"^\d{4}-\d{2}$"),
    db: Session = Depends(get_db),
) -> BillingSummaryResponse:
    return _service(db).admin_billing_summary(month)


@router.get("/audit-logs", response_model=List[AuditLogItem])
def list_audit_logs(
    db: Session = Depends(get_db),
    limit: int = Query(50, ge=1, le=200),
    tenant_id: int | None = Query(default=None, ge=1),
) -> List[AuditLogItem]:
    return _service(db).list_audit_logs(limit, tenant_id)


@router.get("/users", response_model=List[PlatformUserItem])
def list_platform_users(db: Session = Depends(get_db)) -> List[PlatformUserItem]:
    return _service(db).list_platform_users()


@router.get("/ai-providers", response_model=List[PlatformAIProviderItem])
def list_platform_ai_providers(
    request: Request,
    db: Session = Depends(get_db),
) -> List[PlatformAIProviderItem]:
    return _service(db, request).list_platform_ai_providers()


@router.post("/ai-providers", response_model=PlatformAIProviderItem, status_code=status.HTTP_201_CREATED)
def create_platform_ai_provider(
    request: Request,
    payload: PlatformAIProviderPayload,
    db: Session = Depends(get_db),
) -> PlatformAIProviderItem:
    return _service(db, request).create_platform_ai_provider(payload)


@router.put("/ai-providers/{provider_id}", response_model=PlatformAIProviderItem)
def update_platform_ai_provider(
    request: Request,
    provider_id: int,
    payload: PlatformAIProviderPayload,
    db: Session = Depends(get_db),
) -> PlatformAIProviderItem:
    return _service(db, request).update_platform_ai_provider(provider_id, payload)


@router.delete("/ai-providers/{provider_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_platform_ai_provider(
    request: Request,
    provider_id: int,
    db: Session = Depends(get_db),
) -> Response:
    _service(db, request).delete_platform_ai_provider(provider_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.put("/tenants/{tenant_id}/settings", response_model=TenantSettingsResponse)
def update_tenant_settings(
    tenant_id: int,
    payload: TenantSettingsPayload,
    db: Session = Depends(get_db),
) -> TenantSettingsResponse:
    return _service(db).update_tenant_settings(tenant_id, payload)


@router.get("/tenants/{tenant_id}/ai-providers", response_model=List[TenantAIProviderItem])
def list_tenant_ai_providers(
    tenant_id: int,
    db: Session = Depends(get_db),
) -> List[TenantAIProviderItem]:
    return _service(db).list_tenant_ai_providers(tenant_id)


@router.post("/tenants/{tenant_id}/ai-providers", response_model=TenantAIProviderItem, status_code=status.HTTP_201_CREATED)
def create_tenant_ai_provider(
    tenant_id: int,
    payload: TenantAIProviderPayload,
    db: Session = Depends(get_db),
) -> TenantAIProviderItem:
    return _service(db).create_tenant_ai_provider(tenant_id, payload)


@router.put("/tenants/{tenant_id}/ai-providers/{provider_id}", response_model=TenantAIProviderItem)
def update_tenant_ai_provider(
    tenant_id: int,
    provider_id: int,
    payload: TenantAIProviderPayload,
    db: Session = Depends(get_db),
) -> TenantAIProviderItem:
    return _service(db).update_tenant_ai_provider(tenant_id, provider_id, payload)


@router.delete("/tenants/{tenant_id}/ai-providers/{provider_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tenant_ai_provider(
    tenant_id: int,
    provider_id: int,
    db: Session = Depends(get_db),
) -> Response:
    _service(db).delete_tenant_ai_provider(tenant_id, provider_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/users/{user_id}/ai-providers", response_model=List[UserAIProviderItem])
def list_user_ai_providers(
    user_id: int,
    db: Session = Depends(get_db),
) -> List[UserAIProviderItem]:
    return _service(db).list_user_ai_providers(user_id)


@router.post("/users/{user_id}/ai-providers", response_model=UserAIProviderItem, status_code=status.HTTP_201_CREATED)
def create_user_ai_provider(
    user_id: int,
    payload: UserAIProviderPayload,
    db: Session = Depends(get_db),
) -> UserAIProviderItem:
    return _service(db).create_user_ai_provider(user_id, payload)


@router.put("/users/{user_id}/ai-providers/{provider_id}", response_model=UserAIProviderItem)
def update_user_ai_provider(
    user_id: int,
    provider_id: int,
    payload: UserAIProviderPayload,
    db: Session = Depends(get_db),
) -> UserAIProviderItem:
    return _service(db).update_user_ai_provider(user_id, provider_id, payload)


@router.delete("/users/{user_id}/ai-providers/{provider_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user_ai_provider(
    user_id: int,
    provider_id: int,
    db: Session = Depends(get_db),
) -> Response:
    _service(db).delete_user_ai_provider(user_id, provider_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
