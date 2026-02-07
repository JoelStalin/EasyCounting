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
