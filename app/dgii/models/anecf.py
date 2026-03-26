"""Anulación e-CF (ANECF) models."""
from __future__ import annotations

from datetime import datetime

from lxml import etree
from pydantic import Field

from typing import ClassVar

from app.dgii.models.base import BaseDGIIModel, XMLSerializerConfig


class ANECFRequest(BaseDGIIModel):
    """Solicita la anulación de una secuencia e-CF."""

    xml_config: ClassVar[XMLSerializerConfig] = XMLSerializerConfig(root_tag="ANECF")

    encf: str = Field(..., max_length=13)
    rnc_emisor: str = Field(..., max_length=11, alias="rncEmisor")
    motivo: str = Field(..., max_length=255)
    fecha_anulacion: datetime = Field(..., alias="fechaAnulacion")

    def _build_tree(self) -> etree._Element:
        root = self._create_root()
        self._build_key_values(
            root,
            [
                ("ENCF", self.encf),
                ("RNCEmisor", self.rnc_emisor),
                ("Motivo", self.motivo),
                ("FechaAnulacion", self.fecha_anulacion.isoformat()),
            ],
        )
        return root
