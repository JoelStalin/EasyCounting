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
