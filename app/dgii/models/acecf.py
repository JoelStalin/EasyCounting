"""Aprobación Comercial e-CF (ACECF) models."""
from __future__ import annotations

from datetime import datetime

from lxml import etree
from pydantic import Field

from typing import ClassVar

from app.dgii.models.base import BaseDGIIModel, XMLSerializerConfig


class ACECFRequest(BaseDGIIModel):
    """Notifica la aprobación comercial del e-CF."""

    xml_config: ClassVar[XMLSerializerConfig] = XMLSerializerConfig(root_tag="ACECF")

    encf: str = Field(..., max_length=13)
    rnc_emisor: str = Field(..., max_length=11, alias="rncEmisor")
    rnc_receptor: str = Field(..., max_length=11, alias="rncReceptor")
    fecha_aprobacion: datetime = Field(..., alias="fechaAprobacion")
    comentario: str = Field(..., max_length=255)

    def _build_tree(self) -> etree._Element:
        root = self._create_root()
        self._build_key_values(
            root,
            [
                ("ENCF", self.encf),
                ("RNCEmisor", self.rnc_emisor),
                ("RNCReceptor", self.rnc_receptor),
                ("FechaAprobacion", self.fecha_aprobacion.isoformat()),
                ("Comentario", self.comentario),
            ],
        )
        return root
