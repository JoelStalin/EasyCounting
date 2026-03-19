from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.application.client_portal import ClientPortalService
from app.application.recurring_invoices import RecurringInvoiceService
from app.application.tenant_api import TenantApiService
from app.application.tenant_chat import TenantChatService
from app.infra.settings import settings as app_settings
from app.portal_client.schemas import (
    ChatAnswerResponse,
    ChatQuestionRequest,
    InvoiceDetailResponse,
    InvoiceListResponse,
    PlanChangeRequest,
    PlanPublic,
    TenantOnboardingStatusResponse,
    TenantOnboardingUpdateRequest,
    TenantPlanSummary,
    UsageListResponse,
)
from app.shared.database import get_db
from app.shared.security import decode_jwt
from app.recurring_invoices.schemas import (
    RecurringInvoiceRunSummary,
    RecurringInvoiceScheduleCreateRequest,
    RecurringInvoiceScheduleItem,
    RecurringInvoiceScheduleUpdateRequest,
)
from app.tenant_api.schemas import (
    TenantApiTokenCreateRequest,
    TenantApiTokenCreateResponse,
    TenantApiTokenItem,
)

router = APIRouter(prefix="/cliente", tags=["Cliente"])


def _require_tenant_user(
    request: Request,
    authorization: str | None = Header(default=None, alias="Authorization"),
) -> dict:
    if app_settings.environment in {"test", "testing"}:
        payload = {"tenant_id": 1, "role": "tenant_user"}
        request.state.tenant_payload = payload
        return payload
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authorization invalido")
    token = authorization.split(" ", 1)[1].strip()
    try:
        payload = decode_jwt(token)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token invalido") from exc
    role = payload.get("role")
    if not isinstance(role, str) or role.startswith("platform_"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acceso restringido a tenants")
    if payload.get("tenant_id") is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Tenant no asociado")
    request.state.tenant_payload = payload
    return payload


def _tenant_id_from_payload(payload: dict) -> int:
    tenant_id = payload.get("tenant_id")
    try:
        return int(tenant_id)
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Tenant invalido") from exc


def _user_id_from_payload(payload: dict) -> int | None:
    user_id = payload.get("sub")
    if user_id is None:
        return None
    try:
        return int(user_id)
    except (TypeError, ValueError):
        return None


@router.get("/health")
def health() -> dict:
    return {"status": "ok", "scope": "cliente"}


@router.get("/me")
def me(payload: dict = Depends(_require_tenant_user)) -> dict:
    return {"user": payload}


@router.get("/onboarding", response_model=TenantOnboardingStatusResponse)
def get_onboarding_status(
    db: Session = Depends(get_db),
    payload: dict = Depends(_require_tenant_user),
) -> TenantOnboardingStatusResponse:
    tenant_id = _tenant_id_from_payload(payload)
    service = ClientPortalService(db)
    return service.get_onboarding_status(tenant_id)


@router.put("/onboarding", response_model=TenantOnboardingStatusResponse)
def complete_onboarding(
    body: TenantOnboardingUpdateRequest,
    db: Session = Depends(get_db),
    payload: dict = Depends(_require_tenant_user),
) -> TenantOnboardingStatusResponse:
    tenant_id = _tenant_id_from_payload(payload)
    service = ClientPortalService(db)
    return service.complete_onboarding(tenant_id, body)


@router.get("/plans", response_model=list[PlanPublic])
def list_plans(
    db: Session = Depends(get_db),
    _payload: dict = Depends(_require_tenant_user),
) -> list[PlanPublic]:
    service = ClientPortalService(db)
    return service.list_plans()


@router.get("/plan", response_model=TenantPlanSummary)
def get_plan(
    db: Session = Depends(get_db),
    payload: dict = Depends(_require_tenant_user),
) -> TenantPlanSummary:
    tenant_id = _tenant_id_from_payload(payload)
    service = ClientPortalService(db)
    return service.get_plan_summary(tenant_id)


@router.put("/plan", response_model=TenantPlanSummary)
def request_plan_change(
    payload: PlanChangeRequest,
    db: Session = Depends(get_db),
    token_payload: dict = Depends(_require_tenant_user),
) -> TenantPlanSummary:
    tenant_id = _tenant_id_from_payload(token_payload)
    service = ClientPortalService(db)
    return service.request_plan_change(tenant_id, payload.plan_id)


@router.get("/usage", response_model=UsageListResponse)
def usage_summary(
    db: Session = Depends(get_db),
    payload: dict = Depends(_require_tenant_user),
    month: str | None = Query(default=None, pattern=r"^\d{4}-\d{2}$"),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
) -> UsageListResponse:
    tenant_id = _tenant_id_from_payload(payload)
    service = ClientPortalService(db)
    return service.usage_summary(tenant_id=tenant_id, month=month, page=page, size=size)


@router.get("/invoices", response_model=InvoiceListResponse)
def list_invoices(
    db: Session = Depends(get_db),
    payload: dict = Depends(_require_tenant_user),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    estado_dgii: str | None = Query(default=None, max_length=30),
    encf: str | None = Query(default=None, max_length=20),
    date_from: datetime | None = Query(default=None),
    date_to: datetime | None = Query(default=None),
) -> InvoiceListResponse:
    tenant_id = _tenant_id_from_payload(payload)
    service = ClientPortalService(db)
    return service.list_invoices(
        tenant_id=tenant_id,
        page=page,
        size=size,
        estado_dgii=estado_dgii,
        encf=encf,
        date_from=date_from,
        date_to=date_to,
    )


@router.get("/invoices/{invoice_id}", response_model=InvoiceDetailResponse)
def get_invoice(
    invoice_id: int,
    db: Session = Depends(get_db),
    payload: dict = Depends(_require_tenant_user),
) -> InvoiceDetailResponse:
    tenant_id = _tenant_id_from_payload(payload)
    service = ClientPortalService(db)
    return service.get_invoice_detail(tenant_id=tenant_id, invoice_id=invoice_id)


@router.get("/api-tokens", response_model=list[TenantApiTokenItem])
def list_api_tokens(
    db: Session = Depends(get_db),
    payload: dict = Depends(_require_tenant_user),
) -> list[TenantApiTokenItem]:
    tenant_id = _tenant_id_from_payload(payload)
    service = TenantApiService(db)
    return service.list_tokens(tenant_id=tenant_id)


@router.post("/api-tokens", response_model=TenantApiTokenCreateResponse, status_code=status.HTTP_201_CREATED)
def create_api_token(
    body: TenantApiTokenCreateRequest,
    db: Session = Depends(get_db),
    payload: dict = Depends(_require_tenant_user),
) -> TenantApiTokenCreateResponse:
    tenant_id = _tenant_id_from_payload(payload)
    service = TenantApiService(db)
    return service.create_token(
        tenant_id=tenant_id,
        created_by_user_id=_user_id_from_payload(payload),
        payload=body,
    )


@router.delete("/api-tokens/{token_id}", response_model=TenantApiTokenItem)
def revoke_api_token(
    token_id: int,
    db: Session = Depends(get_db),
    payload: dict = Depends(_require_tenant_user),
) -> TenantApiTokenItem:
    tenant_id = _tenant_id_from_payload(payload)
    service = TenantApiService(db)
    return service.revoke_token(tenant_id=tenant_id, token_id=token_id)


@router.get("/recurring-invoices", response_model=list[RecurringInvoiceScheduleItem])
def list_recurring_invoices(
    db: Session = Depends(get_db),
    payload: dict = Depends(_require_tenant_user),
) -> list[RecurringInvoiceScheduleItem]:
    tenant_id = _tenant_id_from_payload(payload)
    service = RecurringInvoiceService(db)
    return service.list_schedules(tenant_id=tenant_id)


@router.post("/recurring-invoices", response_model=RecurringInvoiceScheduleItem, status_code=status.HTTP_201_CREATED)
def create_recurring_invoice(
    body: RecurringInvoiceScheduleCreateRequest,
    db: Session = Depends(get_db),
    payload: dict = Depends(_require_tenant_user),
) -> RecurringInvoiceScheduleItem:
    tenant_id = _tenant_id_from_payload(payload)
    service = RecurringInvoiceService(db)
    return service.create_schedule(
        tenant_id=tenant_id,
        created_by_user_id=_user_id_from_payload(payload),
        payload=body,
    )


@router.put("/recurring-invoices/{schedule_id}", response_model=RecurringInvoiceScheduleItem)
def update_recurring_invoice(
    schedule_id: int,
    body: RecurringInvoiceScheduleUpdateRequest,
    db: Session = Depends(get_db),
    payload: dict = Depends(_require_tenant_user),
) -> RecurringInvoiceScheduleItem:
    tenant_id = _tenant_id_from_payload(payload)
    service = RecurringInvoiceService(db)
    return service.update_schedule(tenant_id=tenant_id, schedule_id=schedule_id, payload=body)


@router.post("/recurring-invoices/{schedule_id}/pause", response_model=RecurringInvoiceScheduleItem)
def pause_recurring_invoice(
    schedule_id: int,
    db: Session = Depends(get_db),
    payload: dict = Depends(_require_tenant_user),
) -> RecurringInvoiceScheduleItem:
    tenant_id = _tenant_id_from_payload(payload)
    service = RecurringInvoiceService(db)
    return service.pause_schedule(tenant_id=tenant_id, schedule_id=schedule_id)


@router.post("/recurring-invoices/{schedule_id}/resume", response_model=RecurringInvoiceScheduleItem)
def resume_recurring_invoice(
    schedule_id: int,
    db: Session = Depends(get_db),
    payload: dict = Depends(_require_tenant_user),
) -> RecurringInvoiceScheduleItem:
    tenant_id = _tenant_id_from_payload(payload)
    service = RecurringInvoiceService(db)
    return service.resume_schedule(tenant_id=tenant_id, schedule_id=schedule_id)


@router.post("/recurring-invoices/run-due", response_model=RecurringInvoiceRunSummary)
def run_due_recurring_invoices(
    db: Session = Depends(get_db),
    payload: dict = Depends(_require_tenant_user),
) -> RecurringInvoiceRunSummary:
    tenant_id = _tenant_id_from_payload(payload)
    service = RecurringInvoiceService(db)
    return service.run_due_schedules(tenant_id=tenant_id)


@router.post("/chat/ask", response_model=ChatAnswerResponse)
def ask_chatbot(
    body: ChatQuestionRequest,
    db: Session = Depends(get_db),
    payload: dict = Depends(_require_tenant_user),
) -> ChatAnswerResponse:
    tenant_id = _tenant_id_from_payload(payload)
    service = TenantChatService(db)
    return service.answer_question(tenant_id=tenant_id, payload=body)
