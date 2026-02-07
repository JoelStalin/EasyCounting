"""Pydantic schemas for RI rendering."""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator

from app.shared.time import utcnow


class RILineItem(BaseModel):
    descripcion: str = Field(..., max_length=200)
    cantidad: Decimal = Field(..., gt=0)
    precio_unitario: Decimal = Field(..., gt=0, alias="precioUnitario")

    @property
    def total(self) -> Decimal:
        return self.cantidad * self.precio_unitario


class RIRequest(BaseModel):
    encf: str = Field(..., max_length=13)
    rnc_emisor: str = Field(..., max_length=11, alias="rncEmisor")
    razon_social_emisor: str = Field(..., max_length=120, alias="razonSocialEmisor")
    rnc_receptor: str = Field(..., max_length=11, alias="rncReceptor")
    razon_social_receptor: str = Field(..., max_length=120, alias="razonSocialReceptor")
    monto_total: Decimal = Field(..., alias="montoTotal")
    fecha_emision: datetime = Field(default_factory=utcnow, alias="fechaEmision")
    items: List[RILineItem] = Field(default_factory=list)
    qr_url: Optional[str] = Field(None, alias="qrUrl")
    direccion_emisor: Optional[str] = Field(None, alias="direccionEmisor", max_length=250)
    direccion_receptor: Optional[str] = Field(None, alias="direccionReceptor", max_length=250)

    @field_validator("items")
    @classmethod
    def _validate_items(cls, value: List[RILineItem]) -> List[RILineItem]:
        if not value:
            raise ValueError("Debe incluir al menos un item para la representación impresa")
        return value
