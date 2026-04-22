from __future__ import annotations

from base64 import b64decode
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import hashlib
import secrets
import binascii
from uuid import uuid4
from pathlib import Path

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.billing.validators import normalize_tipo_ecf, validate_encf_for_tipo
from app.models.invoice import Invoice, InvoiceLine
from app.models.sequence import Sequence
from app.models.tenant import Tenant
from app.models.tenant_api_token import TenantApiToken
from app.ri.render import build_context, render_pdf
from app.ri.schemas import RIRequest, RILineItem
from app.services.email_service import EmailAttachment, EmailPayload, get_email_service
from app.shared.storage import storage
from app.tenant_api.schemas import (
    TenantApiInvoiceLineInput,
    TenantApiInvoiceCreateRequest,
    TenantApiInvoiceCreateResponse,
    TenantApiInvoiceDetailResponse,
    TenantApiInvoiceItem,
    TenantApiInvoiceListResponse,
    TenantApiTokenCreateRequest,
    TenantApiTokenCreateResponse,
    TenantApiTokenItem,
)

TOKEN_PREFIX = "gtu_tnt_"
READ_SCOPE = "invoices:read"
WRITE_SCOPE = "invoices:write"


class TenantApiService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_tokens(self, *, tenant_id: int) -> list[TenantApiTokenItem]:
        tokens = self.db.scalars(
            select(TenantApiToken).where(TenantApiToken.tenant_id == tenant_id).order_by(TenantApiToken.created_at.desc())
        ).all()
        return [self._serialize_token(token) for token in tokens]

    def create_token(
        self,
        *,
        tenant_id: int,
        created_by_user_id: int | None,
        payload: TenantApiTokenCreateRequest,
    ) -> TenantApiTokenCreateResponse:
        self._get_tenant(tenant_id)
        raw_token = f"{TOKEN_PREFIX}{secrets.token_urlsafe(32)}"
        scopes = [READ_SCOPE] if payload.access_mode == "read" else [READ_SCOPE, WRITE_SCOPE]
        expires_at = None
        if payload.expires_in_days:
            expires_at = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=payload.expires_in_days)
        record = TenantApiToken(
            tenant_id=tenant_id,
            created_by_user_id=created_by_user_id,
            name=payload.name.strip(),
            token_prefix=raw_token[:18],
            token_hash=self._digest(raw_token),
            scopes=",".join(scopes),
            expires_at=expires_at,
        )
        self.db.add(record)
        self.db.flush()
        return TenantApiTokenCreateResponse(**self._serialize_token(record).model_dump(by_alias=True), token=raw_token)

    def revoke_token(self, *, tenant_id: int, token_id: int) -> TenantApiTokenItem:
        token = self.db.get(TenantApiToken, token_id)
        if not token or token.tenant_id != tenant_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Token API no encontrado")
        token.revoked_at = datetime.now(timezone.utc).replace(tzinfo=None)
        self.db.flush()
        return self._serialize_token(token)

    def authenticate_token(self, raw_token: str, *, required_scope: str) -> TenantApiToken:
        record = self.db.scalar(select(TenantApiToken).where(TenantApiToken.token_hash == self._digest(raw_token)))
        if not record:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="API token invalido")
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        if record.revoked_at:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="API token revocado")
        if record.expires_at and record.expires_at < now:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="API token expirado")
        if required_scope not in self._parse_scopes(record.scopes):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Scope insuficiente para esta operacion")
        record.last_used_at = now
        self.db.flush()
        return record

    def list_invoices(
        self,
        *,
        tenant_id: int,
        page: int,
        size: int,
        encf: str | None = None,
        estado_dgii: str | None = None,
    ) -> TenantApiInvoiceListResponse:
        stmt = select(Invoice).where(Invoice.tenant_id == tenant_id)
        if encf:
            stmt = stmt.where(Invoice.encf == encf)
        if estado_dgii:
            stmt = stmt.where(Invoice.estado_dgii == estado_dgii)
        total = self.db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
        invoices = self.db.scalars(stmt.order_by(Invoice.fecha_emision.desc()).offset((page - 1) * size).limit(size)).all()
        return TenantApiInvoiceListResponse(
            items=[self._serialize_invoice_item(invoice) for invoice in invoices],
            total=int(total),
            page=page,
            size=size,
        )

    def get_invoice_detail(self, *, tenant_id: int, invoice_id: int) -> TenantApiInvoiceDetailResponse:
        invoice = self.db.get(Invoice, invoice_id)
        if not invoice or invoice.tenant_id != tenant_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Factura no encontrada")
        item = self._serialize_invoice_item(invoice).model_dump(by_alias=True)
        return TenantApiInvoiceDetailResponse(
            **item,
            xmlPath=invoice.xml_path,
            xmlHash=invoice.xml_hash,
            codigoSeguridad=invoice.codigo_seguridad,
            contabilizado=bool(invoice.contabilizado),
            accountedAt=invoice.accounted_at,
            asientoReferencia=invoice.asiento_referencia,
        )

    def create_invoice(self, *, tenant_id: int, payload: TenantApiInvoiceCreateRequest) -> TenantApiInvoiceCreateResponse:
        tenant = self._get_tenant(tenant_id)
        if tenant.onboarding_status != "completed":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="El tenant aun no completa su setup fiscal y no puede registrar facturas por API",
            )

        issued_at = (payload.fecha_emision or datetime.now(timezone.utc)).replace(tzinfo=None)
        tipo_ecf = self._normalize_tipo_ecf(payload.tipo_ecf)
        if payload.encf:
            try:
                encf = self._normalize_encf(payload.encf, tipo_ecf=tipo_ecf)
            except ValueError as exc:
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
        else:
            encf = self._allocate_encf(tenant_id=tenant_id, tipo_ecf=tipo_ecf)
        if payload.xml_signed_base64:
            try:
                b64decode(payload.xml_signed_base64, validate=True)
            except (binascii.Error, ValueError) as exc:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="El XML firmado en base64 no es valido",
                ) from exc
        subtotal, tax_total, computed_total = self._compute_totals(payload.line_items)
        track_id = f"tenant-api-{uuid4().hex[:12]}"
        relative_path = f"tenant-api/{tenant_id}/{encf}.json"
        stored_payload = {
            "source": "tenant_api",
            "encf": encf,
            "tipo_ecf": tipo_ecf,
            "rnc_receptor": payload.rnc_receptor,
            "receptor_nombre": payload.receptor_nombre,
            "receptor_email": payload.receptor_email,
            "total": str(payload.total),
            "subtotal": str(subtotal),
            "tax_total": str(tax_total),
            "line_items": [line.model_dump(by_alias=True, mode="json") for line in payload.line_items],
            "fecha_emision": issued_at.isoformat(),
            "xml_signed_base64": payload.xml_signed_base64,
        }
        try:
            storage.store_json(relative_path, stored_payload)
        except FileExistsError as exc:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Ya existe un payload almacenado para ese e-CF") from exc
        xml_hash = storage.compute_hash(relative_path)

        invoice = Invoice(
            tenant_id=tenant_id,
            encf=encf,
            tipo_ecf=tipo_ecf,
            rnc_receptor=payload.rnc_receptor,
            receptor_nombre=payload.receptor_nombre,
            xml_path=relative_path,
            xml_hash=xml_hash,
            estado_dgii="REGISTRADO_API",
            track_id=track_id,
            codigo_seguridad=None,
            subtotal_source=subtotal,
            tax_total_source=tax_total,
            total_fiscal=computed_total,
            total_accounting=computed_total,
            total=float(Decimal(str(payload.total))),
            fecha_emision=issued_at,
        )
        self.db.add(invoice)
        try:
            self.db.flush()
        except IntegrityError as exc:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="El e-CF ya existe para este tenant") from exc

        self._persist_invoice_lines(invoice=invoice, tenant_id=tenant_id, line_items=payload.line_items)
        self._ensure_ri_pdf(invoice=invoice, tenant=tenant)

        return TenantApiInvoiceCreateResponse(
            invoiceId=invoice.id,
            tenantId=tenant_id,
            encf=invoice.encf,
            estadoDgii=invoice.estado_dgii,
            trackId=track_id,
            total=Decimal(str(invoice.total)),
            message="Factura registrada por API empresarial.",
        )

    def _serialize_token(self, token: TenantApiToken) -> TenantApiTokenItem:
        created_by_email = token.created_by_user.email if token.created_by_user else None
        return TenantApiTokenItem(
            id=token.id,
            name=token.name,
            tokenPrefix=f"{token.token_prefix}...",
            scopes=self._parse_scopes(token.scopes),
            lastUsedAt=token.last_used_at,
            expiresAt=token.expires_at,
            revokedAt=token.revoked_at,
            createdAt=token.created_at,
            createdByEmail=created_by_email,
        )

    @staticmethod
    def _serialize_invoice_item(invoice: Invoice) -> TenantApiInvoiceItem:
        return TenantApiInvoiceItem(
            id=invoice.id,
            encf=invoice.encf,
            tipoEcf=invoice.tipo_ecf,
            estadoDgii=invoice.estado_dgii,
            trackId=invoice.track_id,
            total=Decimal(str(invoice.total)),
            fechaEmision=invoice.fecha_emision,
        )

    def _get_tenant(self, tenant_id: int) -> Tenant:
        tenant = self.db.get(Tenant, tenant_id)
        if not tenant:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant no encontrado")
        return tenant

    @staticmethod
    def _parse_scopes(raw: str) -> list[str]:
        return [item for item in (segment.strip() for segment in raw.split(",")) if item]

    @staticmethod
    def _digest(value: str) -> str:
        return hashlib.sha256(value.encode("utf-8")).hexdigest()

    @staticmethod
    def _normalize_tipo_ecf(raw: str) -> str:
        return normalize_tipo_ecf(raw)

    @staticmethod
    def _normalize_encf(raw: str, *, tipo_ecf: str) -> str:
        value = (raw or "").strip().upper()
        validate_encf_for_tipo(value, tipo_ecf)
        return value

    def _allocate_encf(self, *, tenant_id: int, tipo_ecf: str) -> str:
        sequence = self.db.scalar(
            select(Sequence).where(Sequence.tenant_id == tenant_id, Sequence.doc_type == tipo_ecf).with_for_update()
        )
        if sequence is None:
            sequence = Sequence(
                tenant_id=tenant_id,
                doc_type=tipo_ecf,
                prefix=f"E{tipo_ecf}",
                next_number=2,
            )
            self.db.add(sequence)
            self.db.flush()
            return f"{sequence.prefix}{str(1).zfill(10)}"
        current = sequence.next_number
        sequence.next_number = current + 1
        self.db.flush()
        return f"{sequence.prefix}{str(current).zfill(10)}"

    @staticmethod
    def _compute_totals(line_items: list[TenantApiInvoiceLineInput]) -> tuple[Decimal, Decimal, Decimal]:
        subtotal = Decimal("0")
        tax_total = Decimal("0")
        total = Decimal("0")
        for line in line_items:
            quantity = Decimal(str(line.cantidad))
            unit = Decimal(str(line.precio_unitario))
            discount = Decimal(str(line.discount_amount))
            line_subtotal = (quantity * unit) - discount
            rate = Decimal(str(line.itbis_rate or Decimal("0")))
            itbis = line_subtotal * rate
            line_total = line_subtotal + itbis
            subtotal += line_subtotal
            tax_total += itbis
            total += line_total
        return subtotal, tax_total, total

    def _persist_invoice_lines(self, *, invoice: Invoice, tenant_id: int, line_items: list[TenantApiInvoiceLineInput]) -> None:
        for idx, line in enumerate(line_items, start=1):
            quantity = Decimal(str(line.cantidad))
            unit = Decimal(str(line.precio_unitario))
            discount = Decimal(str(line.discount_amount))
            line_subtotal = (quantity * unit) - discount
            itbis_rate = Decimal(str(line.itbis_rate or Decimal("0")))
            itbis_amount = line_subtotal * itbis_rate
            item = InvoiceLine(
                tenant_id=tenant_id,
                invoice_id=invoice.id,
                line_number=idx,
                cantidad=quantity,
                descripcion=line.descripcion,
                unidad_medida=line.unidad_medida,
                precio_unitario=unit,
                discount_amount=discount,
                line_subtotal=line_subtotal,
                itbis_rate=itbis_rate,
                itbis_amount=itbis_amount,
                line_total=line_subtotal + itbis_amount,
            )
            self.db.add(item)
        self.db.flush()

    def _ensure_ri_pdf(self, *, invoice: Invoice, tenant: Tenant) -> None:
        if invoice.ri_pdf_path:
            return
        ri_request = RIRequest(
            encf=invoice.encf,
            rncEmisor=tenant.rnc,
            razonSocialEmisor=tenant.name,
            rncReceptor=invoice.rnc_receptor or "00000000000",
            razonSocialReceptor=invoice.receptor_nombre or "Consumidor final",
            montoTotal=Decimal(str(invoice.total)),
            fechaEmision=invoice.fecha_emision,
            items=[
                RILineItem(
                    descripcion=line.descripcion,
                    cantidad=Decimal(str(line.cantidad)),
                    precioUnitario=Decimal(str(line.precio_unitario)),
                )
                for line in invoice.line_items
            ]
            or [RILineItem(descripcion="Servicio general", cantidad=Decimal("1"), precioUnitario=Decimal(str(invoice.total)))],
        )
        context = build_context(ri_request)
        pdf_bytes = render_pdf(context)
        relative_pdf = f"ri/{invoice.tenant_id}/{invoice.encf}.pdf"
        try:
            storage.store_bytes(relative_pdf, pdf_bytes)
        except FileExistsError:
            pass
        invoice.ri_pdf_path = relative_pdf
        invoice.ri_generated_at = datetime.now(timezone.utc).replace(tzinfo=None)
        self.db.flush()

    def send_invoice_email(self, *, tenant_id: int, invoice_id: int, recipient: str) -> None:
        invoice = self.db.get(Invoice, invoice_id)
        if not invoice or invoice.tenant_id != tenant_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Factura no encontrada")
        tenant = self._get_tenant(tenant_id)
        self._ensure_ri_pdf(invoice=invoice, tenant=tenant)
        attachments: list[EmailAttachment] = []
        xml_path = storage.resolve_path(invoice.xml_path)
        if xml_path.exists():
            attachments.append(EmailAttachment.from_path(xml_path, content_type="application/json"))
        if invoice.ri_pdf_path:
            pdf_path = storage.resolve_path(invoice.ri_pdf_path)
            if pdf_path.exists():
                attachments.append(EmailAttachment.from_path(pdf_path, content_type="application/pdf"))
        subject = f"EasyCounting | Factura {invoice.encf}"
        body = (
            f"Hola,\n\n"
            f"Compartimos la factura {invoice.encf} ({invoice.tipo_ecf}) por un total de RD$ {Decimal(str(invoice.total)):.2f}.\n"
            f"TrackId: {invoice.track_id or 'N/A'}\n\n"
            f"Este correo fue generado por EasyCounting."
        )
        get_email_service().send(
            EmailPayload(
                to=[recipient],
                subject=subject,
                text_body=body,
                attachments=attachments,
            )
        )
