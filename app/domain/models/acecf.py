"""Pydantic model for ACECF."""
from __future__ import annotations

from datetime import datetime

from lxml import etree
from lxml.builder import E
from pydantic import BaseModel, Field

from app.shared.time import utcnow

class ACECF(BaseModel):
    ENCF: str = Field(..., max_length=13)
    RNCEmisor: str = Field(..., max_length=11)
    RNCComprador: str = Field(..., max_length=11)
    Estado: str = Field(..., max_length=1)
    Motivo: str = Field(..., max_length=255)
    FechaAprobacion: datetime = Field(default_factory=utcnow)

    def to_xml(self) -> bytes:
        doc = E.ACECF(
            E.ENCF(self.ENCF),
            E.RNCEmisor(self.RNCEmisor),
            E.RNCComprador(self.RNCComprador),
            E.Estado(self.Estado),
            E.Motivo(self.Motivo),
            E.FechaAprobacion(self.FechaAprobacion.isoformat()),
        )
        return etree.tostring(doc, encoding="UTF-8", xml_declaration=True)
