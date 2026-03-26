"""RFCE (Resumen Factura Consumo Electrónica) models."""
from __future__ import annotations

from datetime import date
from decimal import Decimal

from lxml import etree
from pydantic import Field

from typing import ClassVar

from app.dgii.models.base import BaseDGIIModel, XMLSerializerConfig, decimal_to_str


class RFCERequest(BaseDGIIModel):
    """Representa el resumen diario/mensual enviado a la DGII."""

    xml_config: ClassVar[XMLSerializerConfig] = XMLSerializerConfig(root_tag="RFCE")

    encf: str = Field(..., max_length=13)
    rnc_emisor: str = Field(..., max_length=11, alias="rncEmisor")
    periodo: date
    cantidad_facturas: int = Field(..., alias="cantidadFacturas", ge=1)
    monto_total: Decimal = Field(..., alias="montoTotal")

    def _build_tree(self) -> etree._Element:
        root = self._create_root()
        self._build_key_values(
            root,
            [
                ("ENCF", self.encf),
                ("RNCEmisor", self.rnc_emisor),
                ("Periodo", self.periodo.isoformat()),
                ("CantidadFacturas", str(self.cantidad_facturas)),
                ("MontoTotal", decimal_to_str(self.monto_total)),
            ],
        )
        return root
