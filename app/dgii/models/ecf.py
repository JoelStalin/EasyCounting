"""Models and XML mapper for e-CF reception payloads."""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import ClassVar, List

from lxml import etree
from pydantic import Field

from app.dgii.models.base import BaseDGIIModel, XMLSerializerConfig, decimal_to_str


class ECFLineItem(BaseDGIIModel):
    """Detalle de producto o servicio dentro del e-CF."""

    xml_config: ClassVar[XMLSerializerConfig] = XMLSerializerConfig(root_tag="Item")

    descripcion: str = Field(..., max_length=200)
    cantidad: Decimal = Field(..., gt=0)
    precio_unitario: Decimal = Field(..., gt=0, alias="precioUnitario")

    def _build_tree(self) -> etree._Element:
        root = self._create_root()
        self._build_key_values(
            root,
            [
                ("Descripcion", self.descripcion),
                ("Cantidad", decimal_to_str(self.cantidad)),
                ("PrecioUnitario", decimal_to_str(self.precio_unitario)),
                ("Total", decimal_to_str(self.cantidad * self.precio_unitario)),
            ],
        )
        return root


class ECFRequest(BaseDGIIModel):
    """Cabecera simplificada compatible con los esquemas de DGII."""

    xml_config: ClassVar[XMLSerializerConfig] = XMLSerializerConfig(root_tag="eCF")

    encf: str = Field(..., max_length=13)
    tipo_ecf: str = Field(..., max_length=6, alias="tipoECF")
    rnc_emisor: str = Field(..., max_length=11, alias="rncEmisor")
    rnc_comprador: str = Field(..., max_length=11, alias="rncComprador")
    fecha_emision: datetime = Field(..., alias="fechaEmision")
    monto_total: Decimal = Field(..., alias="montoTotal")
    moneda: str = Field("DOP", max_length=3)
    items: List[ECFLineItem] = Field(default_factory=list)

    def _build_tree(self) -> etree._Element:
        root = self._create_root()
        encabezado = etree.SubElement(root, "Encabezado")
        self._build_key_values(
            encabezado,
            [
                ("ENCF", self.encf),
                ("TipoECF", self.tipo_ecf),
                ("RNCEmisor", self.rnc_emisor),
                ("RNCComprador", self.rnc_comprador),
                ("FechaEmision", self.fecha_emision.isoformat()),
                ("MontoTotal", decimal_to_str(self.monto_total)),
                ("Moneda", self.moneda),
            ],
        )

        if self.items:
            detalle = etree.SubElement(root, "Detalle")
            for item in self.items:
                detalle.append(item._build_tree())
        return root
