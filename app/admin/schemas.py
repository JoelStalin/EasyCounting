"""Esquemas Pydantic para panel administrativo."""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field
from pydantic.alias_generators import to_camel
from pydantic.config import ConfigDict


class TenantSettingsPayload(BaseModel):
    moneda: str = Field(default="DOP", max_length=5)
    cuenta_ingresos: Optional[str] = Field(default=None, max_length=64)
    cuenta_itbis: Optional[str] = Field(default=None, max_length=64)
    cuenta_retenciones: Optional[str] = Field(default=None, max_length=64)
    dias_credito: int = Field(default=0, ge=0, le=365)
    correo_facturacion: Optional[str] = Field(default=None, max_length=255)
    telefono_contacto: Optional[str] = Field(default=None, max_length=25)
    notas: Optional[str] = Field(default=None, max_length=512)


class TenantSettingsResponse(TenantSettingsPayload):
    updated_at: datetime


class TenantCreate(BaseModel):
    name: str = Field(..., max_length=255)
    rnc: str = Field(..., max_length=11)
    env: str = Field(default="testecf", max_length=20)
    dgii_base_ecf: Optional[str] = Field(default=None, max_length=255)
    dgii_base_fc: Optional[str] = Field(default=None, max_length=255)


class TenantItem(BaseModel):
    id: int
    name: str
    rnc: str
    env: str
    status: str


class LedgerEntryBase(BaseModel):
    referencia: str = Field(..., max_length=64)
    cuenta: str = Field(..., max_length=64)
    descripcion: Optional[str] = Field(default=None, max_length=255)
    debit: Decimal = Field(default=Decimal("0"), ge=Decimal("0"))
    credit: Decimal = Field(default=Decimal("0"), ge=Decimal("0"))
    fecha: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class LedgerEntryCreate(LedgerEntryBase):
    invoice_id: Optional[int] = None


class LedgerEntryItem(LedgerEntryBase):
    id: int
    invoice_id: Optional[int]
    encf: Optional[str]

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, from_attributes=True)


class LedgerPaginatedResponse(BaseModel):
    items: List[LedgerEntryItem]
    total: int
    page: int
    size: int


class LedgerStatusBreakdown(BaseModel):
    contabilizados: int
    pendientes: int


class LedgerTotals(BaseModel):
    total_emitidos: int
    total_aceptados: int
    total_rechazados: int
    total_monto: Decimal


class LedgerMonthlyStat(BaseModel):
    periodo: str
    cantidad: int
    monto: Decimal


class LedgerSummaryResponse(BaseModel):
    totales: LedgerTotals
    contabilidad: LedgerStatusBreakdown
    series: List[LedgerMonthlyStat]


class PlanBase(BaseModel):
    name: str = Field(..., max_length=120)
    precio_mensual: Decimal = Field(default=Decimal("0"), ge=Decimal("0"))
    precio_por_documento: Decimal = Field(default=Decimal("0"), ge=Decimal("0"))
    documentos_incluidos: int = Field(default=0, ge=0)
    descripcion: Optional[str] = Field(default=None, max_length=255)


class PlanCreate(PlanBase):
    pass


class PlanUpdate(BaseModel):
    name: Optional[str] = Field(default=None, max_length=120)
    precio_mensual: Optional[Decimal] = Field(default=None, ge=Decimal("0"))
    precio_por_documento: Optional[Decimal] = Field(default=None, ge=Decimal("0"))
    documentos_incluidos: Optional[int] = Field(default=None, ge=0)
    descripcion: Optional[str] = Field(default=None, max_length=255)


class PlanResponse(PlanBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TenantPlanAssignment(BaseModel):
    plan_id: Optional[int] = Field(default=None, ge=1)


class BillingSummaryItem(BaseModel):
    client_id: int
    client_name: str
    invoice_count: int
    total_amount_due: Decimal


class BillingSummaryResponse(BaseModel):
    month: str
    generated_at: datetime
    items: List[BillingSummaryItem]
    total_amount_due: Decimal


class TenantPlanResponse(BaseModel):
    tenant_id: int
    plan: Optional[PlanResponse] = None


class AuditLogItem(BaseModel):
    id: int
    tenant_id: int
    actor: str
    action: str
    resource: str
    hash_prev: str
    hash_curr: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PlatformUserItem(BaseModel):
    id: int
    email: str
    role: str
    scope: str


class DashboardKpisResponse(BaseModel):
    month: str
    generated_at: datetime
    companies_active: int
    invoices_month: int
    invoices_accepted: int
    invoices_rejected: int
    invoices_other: int
    amount_due_month: Decimal


class InvoiceListItem(BaseModel):
    id: int
    tenant_id: int
    tenant_name: str
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

