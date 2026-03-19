"""Esquemas Pydantic para portal cliente."""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field
from pydantic.config import ConfigDict


class PlanPublic(BaseModel):
    id: int
    name: str = Field(..., max_length=120)
    precio_mensual: Decimal
    precio_por_documento: Decimal
    documentos_incluidos: int
    max_facturas_mes: int
    max_facturas_por_receptor_mes: int
    max_monto_por_factura: Decimal
    includes_recurring_invoices: bool = False
    descripcion: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TenantPlanSummary(BaseModel):
    tenant_id: int
    current_plan: Optional[PlanPublic] = None
    pending_plan: Optional[PlanPublic] = None
    pending_effective_at: Optional[datetime] = None
    pending_requested_at: Optional[datetime] = None


class PlanChangeRequest(BaseModel):
    plan_id: int = Field(..., ge=1)


class UsageSummary(BaseModel):
    month: str
    total_used: int
    included_documents: int
    remaining_documents: int
    total_amount: Decimal


class UsageInvoiceItem(BaseModel):
    usage_id: int
    invoice_id: Optional[int]
    encf: Optional[str]
    tipo_ecf: Optional[str]
    estado_dgii: Optional[str]
    total: Optional[Decimal]
    monto_cargado: Decimal
    fecha_emision: Optional[datetime]
    fecha_uso: datetime


class UsageListResponse(BaseModel):
    summary: UsageSummary
    items: List[UsageInvoiceItem]
    total: int
    page: int
    size: int


class InvoiceListItem(BaseModel):
    id: int
    encf: str
    tipo_ecf: str
    estado_dgii: str
    track_id: Optional[str] = None
    total: Decimal
    fecha_emision: datetime


class InvoiceListResponse(BaseModel):
    items: List[InvoiceListItem]
    total: int
    page: int
    size: int


class InvoiceDetailResponse(InvoiceListItem):
    xml_path: str
    xml_hash: str
    codigo_seguridad: Optional[str] = None
    contabilizado: bool
    accounted_at: Optional[datetime] = None
    asiento_referencia: Optional[str] = None


class ChatQuestionRequest(BaseModel):
    question: str = Field(..., min_length=4, max_length=1500)
    max_sources: int = Field(default=3, ge=1, le=8)


class ChatPreprocessMetadata(BaseModel):
    original_question: str = Field(alias="originalQuestion")
    normalized_question: str = Field(alias="normalizedQuestion")
    normalized_changed: bool = Field(alias="normalizedChanged")
    intent: str
    dispatch_strategy: str = Field(alias="dispatchStrategy")
    provider_skipped_to_save_credits: bool = Field(alias="providerSkippedToSaveCredits")
    reasons: List[str] = Field(default_factory=list)

    model_config = ConfigDict(populate_by_name=True)


class ChatSource(BaseModel):
    invoice_id: int
    encf: str
    track_id: Optional[str] = None
    estado_dgii: str
    total: Decimal
    fecha_emision: datetime
    snippet: str


class ChatAnswerResponse(BaseModel):
    answer: str
    engine: str
    tenant_id: int
    sources: List[ChatSource]
    warnings: List[str] = Field(default_factory=list)
    preprocess: ChatPreprocessMetadata | None = None


class TenantOnboardingStatusResponse(BaseModel):
    tenant_id: int = Field(alias="tenantId")
    onboarding_status: str = Field(alias="onboardingStatus")
    company_name: str = Field(alias="companyName")
    rnc: str
    contact_email: Optional[str] = Field(default=None, alias="contactEmail")
    contact_phone: Optional[str] = Field(default=None, alias="contactPhone")
    notes: Optional[str] = None
    can_emit_real: bool = Field(default=False, alias="canEmitReal")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class TenantOnboardingUpdateRequest(BaseModel):
    company_name: str = Field(..., min_length=2, max_length=255, alias="companyName")
    rnc: str = Field(..., min_length=9, max_length=11)
    contact_email: Optional[str] = Field(default=None, max_length=255, alias="contactEmail")
    contact_phone: Optional[str] = Field(default=None, max_length=25, alias="contactPhone")
    notes: Optional[str] = Field(default=None, max_length=512)

    model_config = ConfigDict(populate_by_name=True)
