"""Odoo integration routes."""
from __future__ import annotations

from datetime import date, datetime, time, timezone
from decimal import Decimal
from typing import List, Optional
import re

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from pydantic.config import ConfigDict
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.application.ecf_submission import submit_ecf
from app.billing.validators import normalize_tipo_ecf, validate_encf_for_tipo
from app.billing.services import BillingService, get_billing_service
from app.dgii.client import DGIIClient
from app.dgii.jobs import dispatcher
from app.dgii.schemas import ECFItem, ECFSubmission, SubmissionResponse
from app.models.sequence import Sequence
from app.models.tenant import Tenant
from app.routers.dependencies import DGIIClientDep
from app.infra.settings import settings
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


class OdooInvoiceBuyer(BaseModel):
    rnc: str
    name: str


class OdooInvoiceLine(BaseModel):
    product_name: str
    quantity: Decimal
    unit_price: Decimal
    itbis_rate: Decimal = Decimal("0")
    discount: Decimal = Decimal("0")

    def to_ecf_item(self) -> ECFItem:
        return ECFItem(
            descripcion=self.product_name,
            cantidad=self.quantity,
            precioUnitario=self.unit_price,
        )


class OdooInvoicePayload(BaseModel):
    tenant_id: int | None = Field(default=None, alias="tenantId")
    odoo_invoice_id: int = Field(alias="odooInvoiceId")
    odoo_invoice_name: str | None = Field(default=None, alias="odooInvoiceName")
    issue_date: date = Field(alias="issueDate")
    e_cf_type: str = Field(alias="eCfType")
    document_number: str | None = Field(default=None, alias="documentNumber")
    issuer_rnc: str | None = Field(default=None, alias="issuerRnc")
    issuer_name: str | None = Field(default=None, alias="issuerName")
    currency: str = "DOP"
    total_amount: Decimal = Field(alias="totalAmount")
    total_itbis: Decimal = Field(default=Decimal("0"), alias="totalItbis")
    total_discount: Decimal = Field(default=Decimal("0"), alias="totalDiscount")
    buyer: Optional[OdooInvoiceBuyer] = None
    lines: List[OdooInvoiceLine]

    model_config = ConfigDict(populate_by_name=True)

    def to_ecf_submission(self, *, issuer_rnc: str, encf: str) -> ECFSubmission:
        receiver_rnc = self.buyer.rnc if self.buyer else "00000000000"
        issue_datetime = datetime.combine(self.issue_date, time.min).replace(tzinfo=timezone.utc).replace(tzinfo=None)
        return ECFSubmission(
            encf=encf,
            tipoECF=self.e_cf_type if self.e_cf_type.startswith("E") else f"E{self.e_cf_type}",
            rncEmisor=issuer_rnc,
            rncReceptor=receiver_rnc,
            fechaEmision=issue_datetime,
            montoTotal=self.total_amount,
            moneda=self.currency,
            items=[line.to_ecf_item() for line in self.lines],
        )


class OdooInvoiceResponse(BaseModel):
    status: str
    certia_track_id: str
    operation_id: str | None = None
    correlation_id: str | None = None
    message: str

    model_config = ConfigDict(populate_by_name=True)


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


def _resolve_tenant(payload: OdooInvoicePayload, db: Session) -> Tenant:
    def _norm_rnc(raw: str | None) -> str | None:
        if not raw:
            return None
        cleaned = re.sub(r"\D", "", raw)
        return cleaned or None

    tenant = None
    if payload.tenant_id is not None:
        tenant = db.get(Tenant, payload.tenant_id)
    normalized_rnc = _norm_rnc(payload.issuer_rnc)
    if tenant is None and normalized_rnc:
        tenant = db.scalar(select(Tenant).where(Tenant.rnc == normalized_rnc))
    if tenant is None:
        raise HTTPException(status_code=400, detail="No se pudo resolver el tenant Odoo: envia tenantId o issuerRnc")
    return tenant


def _allocate_encf(db: Session, *, tenant_id: int, tipo_ecf: str) -> str:
    sequence = db.scalar(
        select(Sequence).where(Sequence.tenant_id == tenant_id, Sequence.doc_type == tipo_ecf).with_for_update()
    )
    if sequence is None:
        sequence = Sequence(
            tenant_id=tenant_id,
            doc_type=tipo_ecf,
            prefix=f"E{tipo_ecf}",
            next_number=2,
        )
        db.add(sequence)
        db.flush()
        return f"{sequence.prefix}{str(1).zfill(10)}"
    current = sequence.next_number
    sequence.next_number = current + 1
    db.flush()
    return f"{sequence.prefix}{str(current).zfill(10)}"


@router.post("/invoices/transmit", response_model=OdooInvoiceResponse, status_code=status.HTTP_202_ACCEPTED)
async def transmit_invoice_from_odoo(
    payload: OdooInvoicePayload,
    client: DGIIClient = DGIIClientDep,
    billing_service: BillingService = Depends(get_billing_service),
    db: Session = Depends(get_db),
) -> OdooInvoiceResponse:
    tenant = _resolve_tenant(payload, db)
    try:
        tipo_ecf = normalize_tipo_ecf(payload.e_cf_type)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    encf_candidate = (payload.document_number or payload.odoo_invoice_name or "").strip().upper()
    if encf_candidate:
        try:
            validate_encf_for_tipo(encf_candidate, tipo_ecf)
            encf = encf_candidate
        except ValueError:
            encf = _allocate_encf(db, tenant_id=tenant.id, tipo_ecf=tipo_ecf)
    else:
        encf = _allocate_encf(db, tenant_id=tenant.id, tipo_ecf=tipo_ecf)

    if settings.odoo_transmit_mock:
        track_id = f"MOCK-{payload.odoo_invoice_id}-{int(datetime.now(timezone.utc).timestamp())}"
        return OdooInvoiceResponse(
            status="RECEIVED",
            certia_track_id=track_id,
            operation_id=None,
            correlation_id=None,
            message=(
                f"Factura Odoo #{payload.odoo_invoice_id} recibida en modo ODOO_TRANSMIT_MOCK "
                f"para tenant {tenant.id}."
            ),
        )

    submission = payload.to_ecf_submission(issuer_rnc=tenant.rnc, encf=encf)
    token = await client.bearer()
    response: SubmissionResponse = await submit_ecf(
        payload=submission,
        token=token,
        client=client,
        billing_service=billing_service,
        db=db,
        dispatcher=dispatcher,
    )
    return OdooInvoiceResponse(
        status="RECEIVED",
        certia_track_id=response.track_id,
        operation_id=response.operation_id,
        correlation_id=response.correlation_id,
        message=f"Factura Odoo #{payload.odoo_invoice_id} encolada y enviada al pipeline DGII.",
    )
