from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


TenantApiScope = Literal["invoices:read", "invoices:write"]


class TenantApiTokenCreateRequest(BaseModel):
    name: str = Field(..., min_length=3, max_length=120)
    access_mode: Literal["read", "read_write"] = Field(default="read", alias="accessMode")
    expires_in_days: int | None = Field(default=90, ge=1, le=3650, alias="expiresInDays")

    model_config = ConfigDict(populate_by_name=True)


class TenantApiTokenItem(BaseModel):
    id: int
    name: str
    token_prefix: str = Field(alias="tokenPrefix")
    scopes: list[TenantApiScope]
    last_used_at: datetime | None = Field(default=None, alias="lastUsedAt")
    expires_at: datetime | None = Field(default=None, alias="expiresAt")
    revoked_at: datetime | None = Field(default=None, alias="revokedAt")
    created_at: datetime = Field(alias="createdAt")
    created_by_email: str | None = Field(default=None, alias="createdByEmail")

    model_config = ConfigDict(populate_by_name=True)


class TenantApiTokenCreateResponse(TenantApiTokenItem):
    token: str


class TenantApiInvoiceItem(BaseModel):
    id: int
    encf: str
    tipo_ecf: str = Field(alias="tipoEcf")
    estado_dgii: str = Field(alias="estadoDgii")
    track_id: str | None = Field(default=None, alias="trackId")
    total: Decimal
    fecha_emision: datetime = Field(alias="fechaEmision")

    model_config = ConfigDict(populate_by_name=True)


class TenantApiInvoiceListResponse(BaseModel):
    items: list[TenantApiInvoiceItem]
    total: int
    page: int
    size: int


class TenantApiInvoiceDetailResponse(TenantApiInvoiceItem):
    xml_path: str = Field(alias="xmlPath")
    xml_hash: str = Field(alias="xmlHash")
    codigo_seguridad: str | None = Field(default=None, alias="codigoSeguridad")
    contabilizado: bool
    accounted_at: datetime | None = Field(default=None, alias="accountedAt")
    asiento_referencia: str | None = Field(default=None, alias="asientoReferencia")


class TenantApiInvoiceCreateRequest(BaseModel):
    encf: str = Field(..., min_length=5, max_length=20)
    tipo_ecf: str = Field(..., min_length=3, max_length=3, alias="tipoEcf")
    rnc_receptor: str | None = Field(default=None, min_length=9, max_length=11, alias="rncReceptor")
    total: Decimal = Field(..., gt=0)
    fecha_emision: datetime | None = Field(default=None, alias="fechaEmision")
    xml_signed_base64: str | None = Field(default=None, alias="xmlSignedBase64", max_length=500000)

    model_config = ConfigDict(populate_by_name=True)


class TenantApiInvoiceCreateResponse(BaseModel):
    invoice_id: int = Field(alias="invoiceId")
    tenant_id: int = Field(alias="tenantId")
    encf: str
    estado_dgii: str = Field(alias="estadoDgii")
    track_id: str = Field(alias="trackId")
    total: Decimal
    message: str

    model_config = ConfigDict(populate_by_name=True)
