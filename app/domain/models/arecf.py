"""Pydantic model for ARECF."""
from __future__ import annotations

from datetime import datetime

from lxml import etree
from lxml.builder import E
from pydantic import BaseModel, Field

from app.shared.time import utcnow

class ARECF(BaseModel):
    ENCF: str = Field(..., max_length=13)
    TrackId: str = Field(..., max_length=64)
    RNCEmisor: str = Field(..., max_length=11)
    RNCComprador: str = Field(..., max_length=11)
    Estado: str = Field(..., max_length=20)
    FechaRecepcion: datetime = Field(default_factory=utcnow)

    def to_xml(self) -> bytes:
        doc = E.ARECF(
            E.ENCF(self.ENCF),
            E.TrackId(self.TrackId),
            E.RNCEmisor(self.RNCEmisor),
            E.RNCComprador(self.RNCComprador),
            E.Estado(self.Estado),
            E.FechaRecepcion(self.FechaRecepcion.isoformat()),
        )
        return etree.tostring(doc, encoding="UTF-8", xml_declaration=True)
