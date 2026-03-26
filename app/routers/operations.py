"""Technical routes for durable fiscal operations."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.application.accounting_sync import OdooAccountingSyncService
from app.application.admin_portal import AdminService
from app.application.fiscal_operations import FiscalOperationService
from app.admin.schemas import OperationDetailResponse, OperationEventItem, OperationListResponse, OperationRetryResponse
from app.dgii.client import DGIIClient
from app.models.fiscal_operation import FiscalOperation
from app.observability.live_stream import stream_operation_events
from app.routers.admin import _require_platform_user
from app.shared.database import get_db


router = APIRouter(prefix="/operations", tags=["Operations"], dependencies=[Depends(_require_platform_user)])


def _platform_payload(request: Request | None) -> dict:
    if request is None:
        return {}
    return getattr(request.state, "platform_payload", {})


def _service(db: Session, request: Request | None = None) -> AdminService:
    return AdminService(db, _platform_payload(request))


@router.get("", response_model=OperationListResponse)
def list_operations(
    request: Request,
    db: Session = Depends(get_db),
    tenant_id: int | None = Query(default=None, ge=1),
    invoice_id: int | None = Query(default=None, ge=1),
    limit: int = Query(default=50, ge=1, le=200),
) -> OperationListResponse:
    return _service(db, request).list_operations(tenant_id=tenant_id, invoice_id=invoice_id, limit=limit)


@router.get("/{operation_id}", response_model=OperationDetailResponse)
def get_operation(
    operation_id: str,
    request: Request,
    db: Session = Depends(get_db),
) -> OperationDetailResponse:
    return _service(db, request).get_operation(operation_id)


@router.get("/{operation_id}/events", response_model=list[OperationEventItem])
def get_operation_events(
    operation_id: str,
    request: Request,
    db: Session = Depends(get_db),
) -> list[OperationEventItem]:
    return _service(db, request).get_operation_events(operation_id)


@router.get("/{operation_id}/stream")
async def get_operation_stream(
    operation_id: str,
    request: Request,
) -> StreamingResponse:
    return StreamingResponse(stream_operation_events(operation_id, request), media_type="text/event-stream")


@router.post("/{operation_id}/retry", response_model=OperationRetryResponse)
async def retry_operation(
    operation_id: str,
    request: Request,
    db: Session = Depends(get_db),
) -> OperationRetryResponse:
    admin_service = _service(db, request)
    base = admin_service.retry_operation(operation_id)
    operation = db.query(FiscalOperation).filter(FiscalOperation.operation_id == operation_id).one()
    operations = FiscalOperationService(db)
    if operation.dgii_track_id:
        async with DGIIClient() as client:
            token = await client.bearer()
            result = await client.get_status(operation.dgii_track_id, token)
        operations.update_remote_status(operation, str(result.get("estado") or result.get("status") or ""), message=str(result.get("descripcion") or result.get("detalle") or "Retry status"))
    if operation.invoice is not None and operation.odoo_sync_state != "SYNCED_TO_ODOO":
        await OdooAccountingSyncService(db).sync_operation(operation)
    db.flush()
    return OperationRetryResponse(
        operation_id=base.operation_id,
        state=operation.state,
        retry_count=operation.retry_count,
    )
