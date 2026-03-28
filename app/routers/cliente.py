from __future__ import annotations

import base64
import binascii
from datetime import datetime

from fastapi import APIRouter, Depends, File, Form, Header, HTTPException, Query, Request, Response, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.application.certificates import TenantCertificateService
from app.application.client_portal import ClientPortalService
from app.application.odoo_mirror import OdooMirrorService
from app.application.recurring_invoices import RecurringInvoiceService
from app.application.tenant_api import TenantApiService
from app.application.tenant_chat import TenantChatService
from app.infra.settings import settings as app_settings
from app.portal_client.schemas import (
    ChatAnswerResponse,
    ChatMessageItem,
    ChatMemoryCreateRequest,
    ChatMemoryItem,
    ChatMemoryUpdateRequest,
    ChatQuestionRequest,
    ChatSessionItem,
    InvoiceDetailResponse,
    InvoiceEmitRequest,
    InvoiceEmitResponse,
    InvoiceListResponse,
    InvoiceSendEmailRequest,
    InvoiceSendEmailResponse,
    OdooInvoiceItem,
    OdooPartnerItem,
    OdooProductItem,
    OdooSyncRequest,
    OdooSyncResponse,
    PlanChangeRequest,
    PlanPublic,
    TenantCertificateListResponse,
    TenantCertificateSignRequest,
    TenantCertificateSignResponse,
    TenantCertificateUploadResponse,
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


def _actor_from_payload(payload: dict) -> str:
    user_id = _user_id_from_payload(payload)
    if user_id is not None:
        return f"user:{user_id}"
    tenant_id = payload.get("tenant_id")
    return f"tenant:{tenant_id}" if tenant_id is not None else "tenant:unknown"


@router.get("/health")
def health() -> dict:
    return {"status": "ok", "scope": "cliente"}


@router.get("/me")
def me(payload: dict = Depends(_require_tenant_user)) -> dict:
    return {"user": payload}


@router.get("/certificates", response_model=TenantCertificateListResponse)
def list_certificates(
    db: Session = Depends(get_db),
    payload: dict = Depends(_require_tenant_user),
) -> TenantCertificateListResponse:
    tenant_id = _tenant_id_from_payload(payload)
    return TenantCertificateService(db).list_certificates(tenant_id)


@router.post("/certificates", response_model=TenantCertificateUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_certificate(
    db: Session = Depends(get_db),
    payload: dict = Depends(_require_tenant_user),
    alias: str = Form(..., max_length=100),
    password: str = Form(..., min_length=1, max_length=512),
    activate: bool = Form(default=True),
    certificate: UploadFile = File(...),
) -> TenantCertificateUploadResponse:
    tenant_id = _tenant_id_from_payload(payload)
    filename = certificate.filename or "certificado.p12"
    suffix = filename.lower()
    if not suffix.endswith(".p12") and not suffix.endswith(".pfx"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Solo se aceptan archivos .p12 o .pfx")
    content = await certificate.read()
    return TenantCertificateService(db).upload_certificate(
        tenant_id=tenant_id,
        alias=alias,
        password=password,
        p12_bytes=content,
        filename=filename,
        activate=activate,
        actor=_actor_from_payload(payload),
        actor_user_id=_user_id_from_payload(payload),
    )


@router.post("/certificates/sign-xml", response_model=TenantCertificateSignResponse)
def sign_xml_with_active_certificate(
    body: TenantCertificateSignRequest,
    db: Session = Depends(get_db),
    payload: dict = Depends(_require_tenant_user),
) -> TenantCertificateSignResponse:
    tenant_id = _tenant_id_from_payload(payload)
    try:
        xml_bytes = base64.b64decode(body.xml)
    except (ValueError, binascii.Error) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="XML base64 invalido") from exc
    signed_xml, runtime = TenantCertificateService(db).sign_xml(
        xml_bytes,
        tenant_id=tenant_id,
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


@router.post("/invoices/emit", response_model=InvoiceEmitResponse, status_code=status.HTTP_201_CREATED)
def emit_invoice(
    body: InvoiceEmitRequest,
    db: Session = Depends(get_db),
    payload: dict = Depends(_require_tenant_user),
) -> InvoiceEmitResponse:
    tenant_id = _tenant_id_from_payload(payload)
    service = ClientPortalService(db)
    result = service.emit_invoice(tenant_id=tenant_id, payload=body)
    return InvoiceEmitResponse.model_validate(result.model_dump(by_alias=True))


@router.get("/invoices/{invoice_id}/pdf")
def download_invoice_pdf(
    invoice_id: int,
    db: Session = Depends(get_db),
    payload: dict = Depends(_require_tenant_user),
) -> FileResponse:
    tenant_id = _tenant_id_from_payload(payload)
    service = ClientPortalService(db)
    detail = service.get_invoice_detail(tenant_id=tenant_id, invoice_id=invoice_id)
    if not detail.ri_pdf_path:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="PDF RI no disponible")
    from app.shared.storage import storage

    path = storage.resolve_path(detail.ri_pdf_path)
    if not path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="PDF RI no encontrado")
    return FileResponse(path=str(path), media_type="application/pdf", filename=f"{detail.encf}.pdf")


@router.get("/invoices/{invoice_id}/xml")
def download_invoice_xml(
    invoice_id: int,
    db: Session = Depends(get_db),
    payload: dict = Depends(_require_tenant_user),
) -> FileResponse:
    tenant_id = _tenant_id_from_payload(payload)
    service = ClientPortalService(db)
    detail = service.get_invoice_detail(tenant_id=tenant_id, invoice_id=invoice_id)
    from app.shared.storage import storage

    path = storage.resolve_path(detail.xml_path)
    if not path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="XML no encontrado")
    return FileResponse(path=str(path), media_type="application/json", filename=f"{detail.encf}.json")


@router.post("/invoices/{invoice_id}/send-email", response_model=InvoiceSendEmailResponse)
def send_invoice_email(
    invoice_id: int,
    body: InvoiceSendEmailRequest,
    db: Session = Depends(get_db),
    payload: dict = Depends(_require_tenant_user),
) -> InvoiceSendEmailResponse:
    tenant_id = _tenant_id_from_payload(payload)
    service = ClientPortalService(db)
    service.send_invoice_email(tenant_id=tenant_id, invoice_id=invoice_id, recipient=body.recipient)
    return InvoiceSendEmailResponse(status="SENT", message="Factura enviada por correo.")


@router.post("/integrations/odoo/sync", response_model=OdooSyncResponse)
async def sync_odoo_data(
    body: OdooSyncRequest,
    db: Session = Depends(get_db),
    payload: dict = Depends(_require_tenant_user),
) -> OdooSyncResponse:
    tenant_id = _tenant_id_from_payload(payload)
    counts = await OdooMirrorService(db).sync(
        tenant_id=tenant_id,
        include_customers=body.include_customers,
        include_vendors=body.include_vendors,
        include_products=body.include_products,
        include_invoices=body.include_invoices,
        limit=body.limit,
    )
    return OdooSyncResponse(
        status="SYNCED",
        customers=counts["customers"],
        vendors=counts["vendors"],
        products=counts["products"],
        invoices=counts["invoices"],
        message="Sincronizacion Odoo completada.",
    )


@router.get("/integrations/odoo/customers", response_model=list[OdooPartnerItem])
def list_odoo_customers(
    db: Session = Depends(get_db),
    payload: dict = Depends(_require_tenant_user),
    limit: int = Query(default=100, ge=1, le=500),
) -> list[OdooPartnerItem]:
    tenant_id = _tenant_id_from_payload(payload)
    rows = OdooMirrorService(db).list_partners(tenant_id=tenant_id, partner_kind="customer", limit=limit)
    return [OdooPartnerItem.model_validate(row, from_attributes=True) for row in rows]


@router.get("/integrations/odoo/vendors", response_model=list[OdooPartnerItem])
def list_odoo_vendors(
    db: Session = Depends(get_db),
    payload: dict = Depends(_require_tenant_user),
    limit: int = Query(default=100, ge=1, le=500),
) -> list[OdooPartnerItem]:
    tenant_id = _tenant_id_from_payload(payload)
    rows = OdooMirrorService(db).list_partners(tenant_id=tenant_id, partner_kind="vendor", limit=limit)
    return [OdooPartnerItem.model_validate(row, from_attributes=True) for row in rows]


@router.get("/integrations/odoo/products", response_model=list[OdooProductItem])
def list_odoo_products(
    db: Session = Depends(get_db),
    payload: dict = Depends(_require_tenant_user),
    limit: int = Query(default=100, ge=1, le=500),
) -> list[OdooProductItem]:
    tenant_id = _tenant_id_from_payload(payload)
    rows = OdooMirrorService(db).list_products(tenant_id=tenant_id, limit=limit)
    return [OdooProductItem.model_validate(row, from_attributes=True) for row in rows]


@router.get("/integrations/odoo/invoices", response_model=list[OdooInvoiceItem])
def list_odoo_invoices(
    db: Session = Depends(get_db),
    payload: dict = Depends(_require_tenant_user),
    limit: int = Query(default=100, ge=1, le=500),
) -> list[OdooInvoiceItem]:
    tenant_id = _tenant_id_from_payload(payload)
    rows = OdooMirrorService(db).list_invoices(tenant_id=tenant_id, limit=limit)
    return [OdooInvoiceItem.model_validate(row, from_attributes=True) for row in rows]


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
async def ask_chatbot(
    body: ChatQuestionRequest,
    db: Session = Depends(get_db),
    payload: dict = Depends(_require_tenant_user),
) -> ChatAnswerResponse:
    tenant_id = _tenant_id_from_payload(payload)
    service = TenantChatService(db)
    return await service.answer_question(tenant_id=tenant_id, user_id=(_user_id_from_payload(payload)), payload=body)


@router.get("/chat/sessions", response_model=list[ChatSessionItem])
def list_chat_sessions(
    db: Session = Depends(get_db),
    payload: dict = Depends(_require_tenant_user),
) -> list[ChatSessionItem]:
    tenant_id = _tenant_id_from_payload(payload)
    user_id = _user_id_from_payload(payload)
    service = ClientPortalService(db)
    return service.list_chat_sessions(tenant_id=tenant_id, user_id=user_id)


@router.get("/chat/sessions/{session_id}/messages", response_model=list[ChatMessageItem])
def get_chat_session_messages(
    session_id: int,
    db: Session = Depends(get_db),
    payload: dict = Depends(_require_tenant_user),
) -> list[ChatMessageItem]:
    tenant_id = _tenant_id_from_payload(payload)
    service = ClientPortalService(db)
    return service.get_chat_session_messages(tenant_id=tenant_id, session_id=session_id)


@router.delete("/chat/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
def delete_chat_session(
    session_id: int,
    db: Session = Depends(get_db),
    payload: dict = Depends(_require_tenant_user),
) -> Response:
    tenant_id = _tenant_id_from_payload(payload)
    service = ClientPortalService(db)
    service.delete_chat_session(tenant_id=tenant_id, session_id=session_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/chat/memory", response_model=list[ChatMemoryItem])
def list_chat_memory(
    db: Session = Depends(get_db),
    payload: dict = Depends(_require_tenant_user),
    limit: int = Query(default=50, ge=1, le=200),
) -> list[ChatMemoryItem]:
    tenant_id = _tenant_id_from_payload(payload)
    user_id = _user_id_from_payload(payload)
    service = ClientPortalService(db)
    return service.list_memory(tenant_id=tenant_id, user_id=user_id, limit=limit)


@router.get("/chat/memory/search", response_model=list[ChatMemoryItem])
def search_chat_memory(
    q: str = Query(..., min_length=2, max_length=500),
    db: Session = Depends(get_db),
    payload: dict = Depends(_require_tenant_user),
    limit: int = Query(default=20, ge=1, le=100),
) -> list[ChatMemoryItem]:
    tenant_id = _tenant_id_from_payload(payload)
    user_id = _user_id_from_payload(payload)
    service = ClientPortalService(db)
    return service.search_memory(tenant_id=tenant_id, query=q, user_id=user_id, limit=limit)


@router.post("/chat/memory", response_model=ChatMemoryItem, status_code=status.HTTP_201_CREATED)
def create_chat_memory(
    body: ChatMemoryCreateRequest,
    db: Session = Depends(get_db),
    payload: dict = Depends(_require_tenant_user),
) -> ChatMemoryItem:
    tenant_id = _tenant_id_from_payload(payload)
    user_id = _user_id_from_payload(payload)
    service = ClientPortalService(db)
    return service.create_memory(tenant_id=tenant_id, user_id=user_id, payload=body)


@router.patch("/chat/memory/{memory_id}", response_model=ChatMemoryItem)
def update_chat_memory(
    memory_id: int,
    body: ChatMemoryUpdateRequest,
    db: Session = Depends(get_db),
    payload: dict = Depends(_require_tenant_user),
) -> ChatMemoryItem:
    tenant_id = _tenant_id_from_payload(payload)
    user_id = _user_id_from_payload(payload)
    service = ClientPortalService(db)
    return service.update_memory(tenant_id=tenant_id, memory_id=memory_id, user_id=user_id, payload=body)


@router.delete("/chat/memory/{memory_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
def delete_chat_memory(
    memory_id: int,
    db: Session = Depends(get_db),
    payload: dict = Depends(_require_tenant_user),
) -> Response:
    tenant_id = _tenant_id_from_payload(payload)
    user_id = _user_id_from_payload(payload)
    service = ClientPortalService(db)
    service.delete_memory(tenant_id=tenant_id, memory_id=memory_id, user_id=user_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
