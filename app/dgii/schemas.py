"""Pydantic schemas for DGII API endpoints."""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.dgii.models import (
    ACECFRequest,
    ANECFRequest,
    ARECFRequest,
    ECFLineItem,
    ECFRequest,
    RFCERequest,
)


class TokenResponse(BaseModel):
    access_token: str
    expires_at: datetime


class SeedResponse(BaseModel):
    seed: str


class ECFItem(BaseModel):
    descripcion: str = Field(..., max_length=200)
    cantidad: Decimal = Field(..., gt=0)
    precio_unitario: Decimal = Field(..., gt=0, alias="precioUnitario")

    def to_model(self) -> ECFLineItem:
        return ECFLineItem(
            descripcion=self.descripcion,
            cantidad=self.cantidad,
            precio_unitario=self.precio_unitario,
        )


class ECFSubmission(BaseModel):
    encf: str = Field(..., max_length=13)
    tipo_ecf: str = Field(..., max_length=6, alias="tipoECF")
    rnc_emisor: str = Field(..., max_length=11, alias="rncEmisor")
    rnc_receptor: str = Field(..., max_length=11, alias="rncReceptor")
    fecha_emision: datetime = Field(..., alias="fechaEmision")
    monto_total: Decimal = Field(..., alias="montoTotal")
    moneda: str = Field("DOP", max_length=3)
    items: List[ECFItem] = Field(default_factory=list)

    def to_model(self) -> ECFRequest:
        return ECFRequest(
            encf=self.encf,
            tipo_ecf=self.tipo_ecf,
            rnc_emisor=self.rnc_emisor,
            rnc_comprador=self.rnc_receptor,
            fecha_emision=self.fecha_emision,
            monto_total=self.monto_total,
            moneda=self.moneda,
            items=[item.to_model() for item in self.items],
        )


class RFCEPayload(BaseModel):
    encf: str = Field(..., max_length=13)
    rnc_emisor: str = Field(..., max_length=11, alias="rncEmisor")
    periodo: date
    cantidad_facturas: int = Field(..., alias="cantidadFacturas", ge=1)
    monto_total: Decimal = Field(..., alias="montoTotal")

    def to_model(self) -> RFCERequest:
        return RFCERequest(
            encf=self.encf,
            rnc_emisor=self.rnc_emisor,
            periodo=self.periodo,
            cantidad_facturas=self.cantidad_facturas,
            monto_total=self.monto_total,
        )


class ANECFPayload(BaseModel):
    encf: str = Field(..., max_length=13)
    rnc_emisor: str = Field(..., max_length=11, alias="rncEmisor")
    motivo: str = Field(..., max_length=255)
    fecha_anulacion: datetime = Field(..., alias="fechaAnulacion")

    def to_model(self) -> ANECFRequest:
        return ANECFRequest(
            encf=self.encf,
            rnc_emisor=self.rnc_emisor,
            motivo=self.motivo,
            fecha_anulacion=self.fecha_anulacion,
        )


class ACECFPayload(BaseModel):
    encf: str = Field(..., max_length=13)
    rnc_emisor: str = Field(..., max_length=11, alias="rncEmisor")
    rnc_receptor: str = Field(..., max_length=11, alias="rncReceptor")
    fecha_aprobacion: datetime = Field(..., alias="fechaAprobacion")
    comentario: str = Field(..., max_length=255)

    def to_model(self) -> ACECFRequest:
        return ACECFRequest(
            encf=self.encf,
            rnc_emisor=self.rnc_emisor,
            rnc_receptor=self.rnc_receptor,
            fecha_aprobacion=self.fecha_aprobacion,
            comentario=self.comentario,
        )


class ARECFPayload(BaseModel):
    encf: str = Field(..., max_length=13)
    track_id: str = Field(..., alias="trackId")
    rnc_emisor: str = Field(..., max_length=11, alias="rncEmisor")
    rnc_receptor: str = Field(..., max_length=11, alias="rncReceptor")
    fecha_recepcion: datetime = Field(..., alias="fechaRecepcion")
    estado: str = Field(..., max_length=20)

    def to_model(self) -> ARECFRequest:
        return ARECFRequest(
            encf=self.encf,
            track_id=self.track_id,
            rnc_emisor=self.rnc_emisor,
            rnc_receptor=self.rnc_receptor,
            fecha_recepcion=self.fecha_recepcion,
            estado=self.estado,
        )


class SubmissionResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    track_id: str = Field(..., alias="trackId")
    status: str
    messages: Optional[List[str]] = None
    operation_id: Optional[str] = Field(default=None, alias="operationId")
    correlation_id: Optional[str] = Field(default=None, alias="correlationId")
    environment: Optional[str] = None
    state: Optional[str] = None


class RFCESubmissionResponse(BaseModel):
    codigo: str
    estado: str
    mensajes: Optional[List[str]] = None
    encf: Optional[str] = None


class StatusResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    track_id: str = Field(..., alias="trackId")
    estado: str
    descripcion: Optional[str] = None
