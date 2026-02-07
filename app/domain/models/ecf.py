"""Pydantic models for e-CF documents."""
from __future__ import annotations

from decimal import Decimal
from typing import List

from lxml import etree
from lxml.builder import E
from pydantic import BaseModel, Field, field_validator


class ECFItem(BaseModel):
    descripcion: str = Field(..., max_length=200)
    cantidad: Decimal = Field(..., gt=0)
    precio_unitario: Decimal = Field(..., gt=0)

    def to_xml_element(self) -> etree._Element:
        total = self.cantidad * self.precio_unitario
        return E.Detalle(
            E.Descripcion(self.descripcion),
            E.Cantidad(f"{self.cantidad:.2f}"),
            E.PrecioUnitario(f"{self.precio_unitario:.2f}"),
            E.Total(f"{total:.2f}"),
        )


class ECFHeader(BaseModel):
    RNCEmisor: str = Field(..., min_length=9, max_length=11)
    RNCComprador: str = Field(..., min_length=9, max_length=11)
    TipoECF: str = Field(default="32", max_length=4)
    ENCF: str = Field(..., min_length=10, max_length=13)
    MontoTotal: Decimal = Field(..., ge=0)


class ECF(BaseModel):
    Encabezado: ECFHeader
    Items: List[ECFItem] = Field(default_factory=list)

    @field_validator("Items")
    @classmethod
    def ensure_items(cls, value: List[ECFItem]) -> List[ECFItem]:
        if not value:
            raise ValueError("Debe incluir al menos un item")
        return value

    def to_xml(self) -> bytes:
        header = self.Encabezado
        items = [item.to_xml_element() for item in self.Items]
        doc = E.eCF(
            E.Encabezado(
                E.RNCEmisor(header.RNCEmisor),
                E.RNCComprador(header.RNCComprador),
                E.TipoECF(header.TipoECF),
                E.ENCF(header.ENCF),
                E.MontoTotal(f"{header.MontoTotal:.2f}"),
            ),
            *items,
        )
        return etree.tostring(doc, encoding="UTF-8", xml_declaration=True)
