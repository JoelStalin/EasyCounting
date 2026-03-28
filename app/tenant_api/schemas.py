from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


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
    encf: str | None = Field(default=None, min_length=5, max_length=20)
    tipo_ecf: str = Field(..., min_length=3, max_length=3, alias="tipoEcf")
    rnc_receptor: str | None = Field(default=None, min_length=9, max_length=11, alias="rncReceptor")
    receptor_nombre: str | None = Field(default=None, max_length=255, alias="receptorNombre")
    receptor_email: str | None = Field(default=None, max_length=255, alias="receptorEmail")
    total: Decimal = Field(..., gt=0)
    fecha_emision: datetime | None = Field(default=None, alias="fechaEmision")
    xml_signed_base64: str | None = Field(default=None, alias="xmlSignedBase64", max_length=500000)
    line_items: list["TenantApiInvoiceLineInput"] = Field(default_factory=list, alias="lineItems")

    model_config = ConfigDict(populate_by_name=True)

    @model_validator(mode="after")
    def _validate_lines(self) -> "TenantApiInvoiceCreateRequest":
        if not self.line_items:
            self.line_items = [
                TenantApiInvoiceLineInput(
                    descripcion="Servicio general",
                    cantidad=Decimal("1"),
                    precioUnitario=self.total,
                )
            ]
        return self


class TenantApiInvoiceLineInput(BaseModel):
    descripcion: str = Field(..., min_length=1, max_length=255)
    cantidad: Decimal = Field(default=Decimal("1"), gt=0)
    precio_unitario: Decimal = Field(..., gt=0, alias="precioUnitario")
    unidad_medida: str | None = Field(default=None, max_length=40, alias="unidadMedida")
    itbis_rate: Decimal | None = Field(default=Decimal("0.18"), alias="itbisRate")
    discount_amount: Decimal = Field(default=Decimal("0"), alias="discountAmount")

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
