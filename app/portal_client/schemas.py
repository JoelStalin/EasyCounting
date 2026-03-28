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
    ri_pdf_path: Optional[str] = None
    receptor_nombre: Optional[str] = None
    receptor_email: Optional[str] = None
    codigo_seguridad: Optional[str] = None
    contabilizado: bool
    accounted_at: Optional[datetime] = None
    asiento_referencia: Optional[str] = None


class InvoiceLineCreateRequest(BaseModel):
    descripcion: str = Field(..., min_length=1, max_length=255)
    cantidad: Decimal = Field(default=Decimal("1"), gt=0)
    precio_unitario: Decimal = Field(..., gt=0, alias="precioUnitario")
    unidad_medida: Optional[str] = Field(default=None, alias="unidadMedida")
    itbis_rate: Optional[Decimal] = Field(default=Decimal("0.18"), alias="itbisRate")
    discount_amount: Decimal = Field(default=Decimal("0"), alias="discountAmount")

    model_config = ConfigDict(populate_by_name=True)


class InvoiceEmitRequest(BaseModel):
    encf: Optional[str] = Field(default=None, min_length=5, max_length=20)
    tipo_ecf: str = Field(..., min_length=2, max_length=3, alias="tipoEcf")
    rnc_receptor: Optional[str] = Field(default=None, min_length=9, max_length=11, alias="rncReceptor")
    receptor_nombre: Optional[str] = Field(default=None, max_length=255, alias="receptorNombre")
    receptor_email: Optional[str] = Field(default=None, max_length=255, alias="receptorEmail")
    total: Decimal = Field(..., gt=0)
    fecha_emision: Optional[datetime] = Field(default=None, alias="fechaEmision")
    line_items: List[InvoiceLineCreateRequest] = Field(default_factory=list, alias="lineItems")
    xml_signed_base64: Optional[str] = Field(default=None, alias="xmlSignedBase64")

    model_config = ConfigDict(populate_by_name=True)


class InvoiceEmitResponse(BaseModel):
    invoice_id: int = Field(alias="invoiceId")
    tenant_id: int = Field(alias="tenantId")
    encf: str
    estado_dgii: str = Field(alias="estadoDgii")
    track_id: str = Field(alias="trackId")
    total: Decimal
    message: str

    model_config = ConfigDict(populate_by_name=True)


class InvoiceSendEmailRequest(BaseModel):
    recipient: str = Field(..., min_length=5, max_length=255)


class InvoiceSendEmailResponse(BaseModel):
    status: str
    message: str


class ChatQuestionRequest(BaseModel):
    question: str = Field(..., min_length=4, max_length=1500)
    max_sources: int = Field(default=3, ge=1, le=8)
    session_id: Optional[int] = Field(default=None, alias="sessionId")

    model_config = ConfigDict(populate_by_name=True)


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
    session_id: Optional[int] = Field(default=None, alias="sessionId")
    sources: List[ChatSource]
    warnings: List[str] = Field(default_factory=list)
    preprocess: ChatPreprocessMetadata | None = None

    model_config = ConfigDict(populate_by_name=True)


class ChatSessionItem(BaseModel):
    id: int
    title: Optional[str]
    created_at: datetime
    updated_at: datetime
    metadata_json: Optional[dict] = Field(default=None, alias="meta")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class ChatMessageItem(BaseModel):
    id: int
    role: str
    content: str
    created_at: datetime
    provider_used: Optional[str] = Field(default=None, alias="provider")
    model_used: Optional[str] = Field(default=None, alias="model")
    latency_ms: Optional[int] = Field(default=None, alias="latencyMs")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class ChatMemoryItem(BaseModel):
    id: int
    scope: str
    memory_type: str = Field(alias="memoryType")
    content: str
    summary: Optional[str] = None
    importance_score: float = Field(alias="importanceScore")
    metadata_json: Optional[dict] = Field(default=None, alias="meta")
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class ChatMemoryCreateRequest(BaseModel):
    scope: str = Field(default="tenant", max_length=40)
    memory_type: str = Field(default="note", max_length=40, alias="memoryType")
    content: str = Field(..., min_length=3, max_length=5000)
    summary: Optional[str] = Field(default=None, max_length=255)
    importance_score: float = Field(default=1.0, ge=0.1, le=10.0, alias="importanceScore")
    metadata_json: Optional[dict] = Field(default=None, alias="meta")

    model_config = ConfigDict(populate_by_name=True)


class ChatMemoryUpdateRequest(BaseModel):
    content: Optional[str] = Field(default=None, min_length=3, max_length=5000)
    summary: Optional[str] = Field(default=None, max_length=255)
    importance_score: Optional[float] = Field(default=None, ge=0.1, le=10.0, alias="importanceScore")
    metadata_json: Optional[dict] = Field(default=None, alias="meta")

    model_config = ConfigDict(populate_by_name=True)


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


class TenantCertificateItem(BaseModel):
    id: int
    alias: str
    subject: str
    issuer: str
    not_before: datetime = Field(alias="notBefore")
    not_after: datetime = Field(alias="notAfter")
    is_active: bool = Field(alias="isActive")

    model_config = ConfigDict(populate_by_name=True)


class TenantCertificateListResponse(BaseModel):
    items: List[TenantCertificateItem]
    active_certificate_id: Optional[int] = Field(default=None, alias="activeCertificateId")
    active_source: Optional[str] = Field(default=None, alias="activeSource")

    model_config = ConfigDict(populate_by_name=True)


class TenantCertificateUploadResponse(TenantCertificateItem):
    message: str


class TenantCertificateSignRequest(BaseModel):
    xml: str = Field(..., description="Documento XML sin firmar en base64")
    reference_uri: str = Field(default="", alias="referenceUri")
    allow_env_fallback: bool = Field(default=True, alias="allowEnvFallback")

    model_config = ConfigDict(populate_by_name=True)


class TenantCertificateSignResponse(BaseModel):
    xml_signed: str = Field(alias="xmlSigned")
    certificate_id: Optional[int] = Field(default=None, alias="certificateId")
    certificate_alias: Optional[str] = Field(default=None, alias="certificateAlias")
    certificate_subject: Optional[str] = Field(default=None, alias="certificateSubject")
    source: str

    model_config = ConfigDict(populate_by_name=True)


class OdooSyncRequest(BaseModel):
    include_customers: bool = Field(default=True, alias="includeCustomers")
    include_vendors: bool = Field(default=True, alias="includeVendors")
    include_products: bool = Field(default=True, alias="includeProducts")
    include_invoices: bool = Field(default=True, alias="includeInvoices")
    limit: int = Field(default=100, ge=1, le=500)

    model_config = ConfigDict(populate_by_name=True)


class OdooSyncResponse(BaseModel):
    status: str
    customers: int
    vendors: int
    products: int
    invoices: int
    message: str


class OdooPartnerItem(BaseModel):
    id: int
    odoo_id: int = Field(alias="odooId")
    partner_kind: str = Field(alias="partnerKind")
    name: str
    vat: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    company_type: Optional[str] = Field(default=None, alias="companyType")
    synced_at: datetime = Field(alias="syncedAt")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class OdooProductItem(BaseModel):
    id: int
    odoo_id: int = Field(alias="odooId")
    name: str
    default_code: Optional[str] = Field(default=None, alias="defaultCode")
    list_price: Decimal = Field(alias="listPrice")
    standard_price: Decimal = Field(alias="standardPrice")
    active: bool
    synced_at: datetime = Field(alias="syncedAt")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class OdooInvoiceItem(BaseModel):
    id: int
    odoo_id: int = Field(alias="odooId")
    move_name: Optional[str] = Field(default=None, alias="moveName")
    move_type: Optional[str] = Field(default=None, alias="moveType")
    state: Optional[str] = None
    payment_state: Optional[str] = Field(default=None, alias="paymentState")
    invoice_date: Optional[datetime] = Field(default=None, alias="invoiceDate")
    partner_name: Optional[str] = Field(default=None, alias="partnerName")
    partner_vat: Optional[str] = Field(default=None, alias="partnerVat")
    amount_total: Decimal = Field(alias="amountTotal")
    amount_tax: Decimal = Field(alias="amountTax")
    amount_untaxed: Decimal = Field(alias="amountUntaxed")
    encf: Optional[str] = None
    synced_at: datetime = Field(alias="syncedAt")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
