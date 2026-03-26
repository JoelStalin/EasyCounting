"""Application service for DGII e-CF submissions."""
from __future__ import annotations

import hashlib
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.application.certificates import TenantCertificateService
from app.application.fiscal_operations import FiscalOperationService
from app.billing.services import BillingError, BillingService
from app.core.logging import bind_request_context
from app.dgii.client import DGIIClient
from app.dgii.jobs import DGIIJobDispatcher
from app.dgii.schemas import ECFSubmission, StatusResponse, SubmissionResponse
from app.dgii.validation import validate_xml
from app.infra.settings import settings
from app.models.invoice import Invoice, InvoiceLine
from app.models.tenant import Tenant
from app.observability.evidence import build_run_directory, write_json_artifact
from app.shared.storage import storage


def _extract_first(payload: dict, keys: list[str], default: str | None = None) -> str | None:
    for key in keys:
        if key in payload and payload[key] is not None:
            return payload[key]
    return default


def build_submission_response(payload: dict) -> SubmissionResponse:
    track_id = _extract_first(payload, ["track_id", "trackId", "track"])
    status_value = _extract_first(payload, ["status", "estado", "respuesta"])
    mensajes = payload.get("mensajes") or payload.get("mensajes_detalle")
    if isinstance(mensajes, str):
        mensajes = [mensajes]
    if not track_id or not status_value:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Respuesta DGII incompleta")
    return SubmissionResponse(track_id=track_id, status=status_value, messages=mensajes)


def build_status_response(track_id: str, payload: dict) -> StatusResponse:
    estado = _extract_first(payload, ["estado", "status"])
    descripcion = _extract_first(payload, ["descripcion", "detalle", "message"], default=None)
    if not estado:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Estado no disponible")
    return StatusResponse(track_id=track_id, estado=estado, descripcion=descripcion)


async def submit_ecf(
    *,
    payload: ECFSubmission,
    token: str,
    client: DGIIClient,
    billing_service: BillingService,
    db: Session,
    dispatcher: DGIIJobDispatcher,
) -> SubmissionResponse:
    tenant = db.scalar(select(Tenant).where(Tenant.rnc == payload.rnc_emisor))
    if not tenant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant no encontrado para el RNC emisor")

    document = payload.to_model()
    xml = document.to_xml_bytes()
    payload_hash = hashlib.sha256(xml).hexdigest()
    bind_request_context(tipo_ecf=document.tipo_ecf, encf=document.encf, tenant_id=tenant.id)
    operations = FiscalOperationService(db)
    operation = operations.start_operation(
        tenant_id=tenant.id,
        document_type=payload.tipo_ecf[:3],
        document_number=payload.encf,
        environment=settings.dgii_env_canonical,
        source_system="EASYCOUNTING",
        payload_hash=payload_hash,
        amount_total=Decimal(str(payload.monto_total)),
        currency=payload.moneda,
        initiated_by=f"tenant:{tenant.id}",
        metadata={"rncEmisor": payload.rnc_emisor, "rncReceptor": payload.rnc_receptor},
    )

    try:
        operations.transition(operation, state="VALIDATING", title="Validando reglas de negocio", stage="VALIDATING")
        billing_service.assert_ecf_allowed(
            rnc=payload.rnc_emisor,
            rnc_receptor=payload.rnc_receptor,
            monto_total=Decimal(str(payload.monto_total)),
            when=payload.fecha_emision,
        )
        validate_xml(xml, "ECF.xsd")

        operations.transition(operation, state="BUILDING_PAYLOAD", title="Construyendo payload fiscal", stage="BUILDING_PAYLOAD")
        signed_xml, signing_runtime = TenantCertificateService(db).sign_dgii_document(
            xml,
            tenant_id=tenant.id,
            allow_env_fallback=True,
        )

        operations.transition(operation, state="SIGNING", title="Documento firmado", stage="SIGNING")
        xml_relative_path = f"xml/{payload.encf}.xml"
        try:
            storage.store_bytes(xml_relative_path, signed_xml)
        except FileExistsError:
            pass
        xml_hash = storage.compute_hash(xml_relative_path)

        run_dir = build_run_directory("dgii_submission")
        write_json_artifact(
            run_dir / f"{operation.operation_id}_request.json",
            {
                "operationId": operation.operation_id,
                "tenantId": tenant.id,
                "encf": payload.encf,
                "tipoECF": payload.tipo_ecf,
                "montoTotal": str(payload.monto_total),
                "currency": payload.moneda,
                "xmlHash": xml_hash,
            },
        )
        operations.register_evidence(
            operation,
            artifact_type="signed_xml",
            file_path=storage.resolve_path(xml_relative_path).as_posix(),
            content_type="application/xml",
            metadata={
                "xmlHash": xml_hash,
                "certificateSource": signing_runtime.source,
                "certificateAlias": signing_runtime.alias,
                "certificateSubject": signing_runtime.subject,
            },
        )

        invoice = db.scalar(select(Invoice).where(Invoice.tenant_id == tenant.id, Invoice.encf == payload.encf))
        if invoice is None:
            invoice = Invoice(
                tenant_id=tenant.id,
                encf=payload.encf,
                tipo_ecf=payload.tipo_ecf[:3],
                rnc_receptor=payload.rnc_receptor,
                receptor_nombre=None,
                xml_path=xml_relative_path,
                xml_hash=xml_hash,
                estado_dgii="QUEUED",
                codigo_seguridad=None,
                currency=payload.moneda,
                subtotal_source=Decimal(str(payload.monto_total)),
                discount_total_source=Decimal("0"),
                tax_total_source=Decimal("0"),
                total_fiscal=Decimal(str(payload.monto_total)),
                total_accounting=Decimal(str(payload.monto_total)),
                rounding_delta=Decimal("0"),
                total=Decimal(str(payload.monto_total)),
                fecha_emision=payload.fecha_emision,
                last_operation_id=operation.id,
            )
            db.add(invoice)
            db.flush()
            line_number = 1
            for item in payload.items:
                quantity = Decimal(str(item.cantidad))
                unit_price = Decimal(str(item.precio_unitario))
                subtotal = quantity * unit_price
                db.add(
                    InvoiceLine(
                        tenant_id=tenant.id,
                        invoice_id=invoice.id,
                        line_number=line_number,
                        descripcion=item.descripcion,
                        cantidad=quantity,
                        precio_unitario=unit_price,
                        discount_amount=Decimal("0"),
                        line_subtotal=subtotal,
                        itbis_rate=None,
                        itbis_amount=Decimal("0"),
                        other_tax_amount=Decimal("0"),
                        line_total=subtotal,
                    )
                )
                line_number += 1
            db.flush()
        else:
            invoice.last_operation_id = operation.id
            invoice.xml_path = xml_relative_path
            invoice.xml_hash = xml_hash
            invoice.currency = payload.moneda
            invoice.total = Decimal(str(payload.monto_total))
            invoice.total_fiscal = Decimal(str(payload.monto_total))
            invoice.total_accounting = Decimal(str(payload.monto_total))
            invoice.subtotal_source = Decimal(str(payload.monto_total))
            db.flush()
        operations.link_invoice(operation, invoice.id)

        operations.transition(
            operation,
            state="SENDING_TO_DGII",
            title="Enviando a DGII",
            stage="SENDING_TO_DGII",
            details={"endpoint": f"{settings.dgii_recepcion_base_url}/ecf"},
        )
        attempt = operations.register_dgii_attempt(
            operation,
            endpoint=f"{settings.dgii_recepcion_base_url}/ecf",
            request_payload_hash=xml_hash,
            request_headers={"Idempotency-Key": operation.operation_key},
        )
        result = await client.send_ecf(
            signed_xml,
            token=token,
            idempotency_key=operation.operation_key,
        )
        response = build_submission_response(result)
        operations.finish_dgii_attempt(
            attempt,
            status="SUCCESS",
            http_status=202,
            response=result,
            track_id=response.track_id,
        )
        operations.transition(
            operation,
            state="DGII_RESPONSE_RECEIVED",
            title="Respuesta inmediata recibida",
            message=response.status,
            stage="DGII_RESPONSE_RECEIVED",
            details=result,
        )
        operation.dgii_track_id = response.track_id
        operation.dgii_status = response.status
        invoice.estado_dgii = str(response.status)
        invoice.track_id = response.track_id
        db.flush()
        operations.transition(
            operation,
            state="TRACKID_REGISTERED",
            title="TrackId registrado",
            message=response.track_id,
            stage="TRACKID_REGISTERED",
            details={"trackId": response.track_id},
        )
        write_json_artifact(
            run_dir / f"{operation.operation_id}_response.json",
            {
                "operationId": operation.operation_id,
                "trackId": response.track_id,
                "status": response.status,
                "messages": response.messages or [],
            },
        )
        operations.register_evidence(
            operation,
            artifact_type="dgii_response",
            file_path=(run_dir / f"{operation.operation_id}_response.json").as_posix(),
            content_type="application/json",
            metadata={"trackId": response.track_id, "status": response.status},
        )

        billing_service.record_usage_for_rnc(
            rnc=payload.rnc_emisor,
            ecf_type=payload.tipo_ecf,
            track_id=response.track_id,
            invoice_id=invoice.id,
        )
        await dispatcher.enqueue_status_check(response.track_id, token, operation.operation_id)
        return SubmissionResponse(
            track_id=response.track_id,
            status=response.status,
            messages=response.messages or [],
            operation_id=operation.operation_id,
            correlation_id=operation.correlation_id,
            environment=operation.environment,
            state=operation.state,
        )
    except BillingError as exc:
        operations.transition(
            operation,
            state="REJECTED",
            title="Validacion de billing rechazada",
            message=str(exc),
            stage="VALIDATING",
            error_code="BILLING_REJECTED",
            error_message=str(exc),
            completed=True,
        )
        raise HTTPException(status_code=status.HTTP_402_PAYMENT_REQUIRED, detail=str(exc)) from exc
    except HTTPException as exc:
        operations.transition(
            operation,
            state="FAILED_TECHNICAL",
            title="Fallo tecnico en flujo DGII",
            message=str(exc.detail),
            error_code=f"HTTP_{exc.status_code}",
            error_message=str(exc.detail),
            completed=True,
        )
        raise
    except Exception as exc:  # noqa: BLE001
        operations.transition(
            operation,
            state="FAILED_TECHNICAL",
            title="Fallo tecnico no controlado",
            message=str(exc),
            error_code=exc.__class__.__name__,
            error_message=str(exc),
            completed=True,
        )
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
