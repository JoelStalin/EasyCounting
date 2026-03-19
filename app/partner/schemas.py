from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field
from pydantic.alias_generators import to_camel
from pydantic.config import ConfigDict


class PartnerProfile(BaseModel):
    account_id: int
    account_name: str
    account_slug: str
    user_email: str
    role: str
    scope: str = "PARTNER"

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class PartnerTenantItem(BaseModel):
    id: int
    name: str
    rnc: str
    env: str
    status: str
    can_emit: bool
    can_manage: bool
    invoice_count: int
    total_amount: Decimal

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class PartnerDashboardResponse(BaseModel):
    partner: PartnerProfile
    tenant_count: int
    invoice_count: int
    accepted_count: int
    pending_count: int
    total_amount: Decimal
    tenants: List[PartnerTenantItem]

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class PartnerTenantOverview(BaseModel):
    tenant: PartnerTenantItem
    accepted_count: int
    rejected_count: int
    last_encf: Optional[str] = None
    last_track_id: Optional[str] = None
    last_invoice_at: Optional[datetime] = None

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class PartnerInvoiceItem(BaseModel):
    id: int
    tenant_id: int
    tenant_name: str
    encf: str
    tipo_ecf: str
    estado_dgii: str
    track_id: Optional[str] = None
    total: Decimal
    fecha_emision: datetime

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class PartnerInvoiceListResponse(BaseModel):
    items: List[PartnerInvoiceItem]
    total: int
    page: int
    size: int

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class PartnerEmitRequest(BaseModel):
    tenant_id: int = Field(..., ge=1)
    encf: str = Field(..., min_length=5, max_length=20)
    tipo_ecf: str = Field(..., min_length=2, max_length=3)
    rnc_receptor: Optional[str] = Field(default=None, max_length=11)
    total: Decimal = Field(..., gt=Decimal("0"))

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class PartnerEmitResponse(BaseModel):
    invoice_id: int
    tenant_id: int
    encf: str
    estado_dgii: str
    track_id: str
    total: Decimal
    message: str

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)
