"""Acuse de Recibo e-CF (ARECF) models."""
from __future__ import annotations

from datetime import datetime

from lxml import etree
from pydantic import Field

from typing import ClassVar

from app.dgii.models.base import BaseDGIIModel, XMLSerializerConfig


class ARECFRequest(BaseDGIIModel):
    """Confirma la recepción de un e-CF por parte del comprador."""

    xml_config: ClassVar[XMLSerializerConfig] = XMLSerializerConfig(root_tag="ARECF")

    encf: str = Field(..., max_length=13)
    track_id: str = Field(..., alias="trackId")
    rnc_emisor: str = Field(..., max_length=11, alias="rncEmisor")
    rnc_receptor: str = Field(..., max_length=11, alias="rncReceptor")
    fecha_recepcion: datetime = Field(..., alias="fechaRecepcion")
    estado: str = Field(..., max_length=20)

    def _build_tree(self) -> etree._Element:
        root = self._create_root()
        self._build_key_values(
            root,
            [
                ("ENCF", self.encf),
                ("TrackId", self.track_id),
                ("RNCEmisor", self.rnc_emisor),
                ("RNCReceptor", self.rnc_receptor),
                ("FechaRecepcion", self.fecha_recepcion.isoformat()),
                ("Estado", self.estado),
            ],
        )
        return root
