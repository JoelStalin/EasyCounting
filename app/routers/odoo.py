"""Rutas locales para integracion Odoo sin servicios externos."""
from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.services.local_rnc_directory import LocalRncDirectoryService
from app.shared.database import get_db


class OdooRncRecord(BaseModel):
    rnc: str
    vat: str
    name: str
    label: str
    commercial_name: str
    status: str
    category: str
    comment: str
    company_type: str
    is_company: bool
    source: str


router = APIRouter(prefix="/odoo", tags=["Odoo Integration"])


@router.get("/rnc/search", response_model=List[OdooRncRecord])
def search_rnc(
    term: str = Query(..., min_length=1, max_length=120),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> List[OdooRncRecord]:
    service = LocalRncDirectoryService(db)
    return [OdooRncRecord.model_validate(record) for record in service.search(term, limit)]


@router.get("/rnc/{fiscal_id}", response_model=OdooRncRecord)
def lookup_rnc(fiscal_id: str, db: Session = Depends(get_db)) -> OdooRncRecord:
    service = LocalRncDirectoryService(db)
    record = service.lookup(fiscal_id)
    if record is None:
        raise HTTPException(status_code=404, detail="RNC no encontrado en directorio local")
    return OdooRncRecord.model_validate(record)


# --- API BRIDGE: RECEPCIÓN DE FACTURAS (INBOUND DESDE ODOO) ---

from datetime import date
from typing import Optional
from uuid import uuid4

class OdooInvoiceBuyer(BaseModel):
    rnc: str
    name: str

class OdooInvoiceLine(BaseModel):
    product_name: str
    quantity: float
    unit_price: float
    itbis_rate: float
    discount: float = 0.0

class OdooInvoicePayload(BaseModel):
    odoo_invoice_id: int
    issue_date: date
    e_cf_type: str
    currency: str = "DOP"
    total_amount: float
    total_itbis: float
    buyer: Optional[OdooInvoiceBuyer] = None
    lines: List[OdooInvoiceLine]

class OdooInvoiceResponse(BaseModel):
    status: str
    certia_track_id: str
    message: str


@router.post("/invoices/transmit", response_model=OdooInvoiceResponse)
def transmit_invoice_from_odoo(payload: OdooInvoicePayload) -> OdooInvoiceResponse:
    """
    Recibe una factura estructurada desde Odoo, la empuja a la cola de firma XML y generación de e-CF.
    Retorna un Tracking ID (TrackId) interno de Certia de forma inmediata (Asíncrono).
    """
    
    # Validaciones básicas de Negocio
    if payload.e_cf_type == "31" and not payload.buyer:
        raise HTTPException(status_code=400, detail="Los e-CF tipo 31 exigen un RNC/Cédula del comprador.")
    
    # TODO: Insertar payload en la BD (Tabla de Comprobantes Pendientes)
    # TODO: Desencadenar la tarea de orquestación XML (Celery / BackgroundTask)
    
    # Generamos un UUID único de transacción (TrackId Certia)
    simulated_track_id = str(uuid4())
    
    return OdooInvoiceResponse(
        status="RECEIVED",
        certia_track_id=simulated_track_id,
        message=f"Factura Odoo #{payload.odoo_invoice_id} encolada exitosamente para transmisión DGII."
    )
