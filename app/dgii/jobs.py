"""Background dispatcher for DGII follow-up jobs."""
from __future__ import annotations

import asyncio
from contextlib import suppress
from typing import Tuple

from sqlalchemy import select

from app.application.accounting_sync import OdooAccountingSyncService
from app.application.fiscal_operations import FiscalOperationService, map_remote_status
from app.core.config import Settings, settings
from app.core.logging import bind_request_context
from app.dgii.client import DGIIClient
from app.models.fiscal_operation import FiscalOperation
from app.models.invoice import Invoice
from app.shared.database import session_scope


QueueItem = Tuple[str, str, str]


class DGIIJobDispatcher:
    def __init__(self, config: Settings | None = None) -> None:
        self.config = config or settings
        self._queue: asyncio.Queue[QueueItem] | None = None
        self._worker: asyncio.Task[None] | None = None
        self._running = False

    async def start(self) -> None:
        if not self.config.jobs_enabled or self._running:
            return
        self._queue = asyncio.Queue()
        self._running = True
        self._worker = asyncio.create_task(self._consume())

    async def stop(self) -> None:
        self._running = False
        if self._worker:
            self._worker.cancel()
            with suppress(asyncio.CancelledError):
                await self._worker
            self._worker = None
        if self._queue is None:
            return
        while not self._queue.empty():
            try:
                self._queue.get_nowait()
                self._queue.task_done()
            except asyncio.QueueEmpty:  # pragma: no cover
                break
        self._queue = None

    async def enqueue_status_check(self, track_id: str, token: str, operation_id: str) -> None:
        if not self.config.jobs_enabled or self._queue is None:
            return
        await self._queue.put((track_id, token, operation_id))

    async def _consume(self) -> None:
        if self._queue is None:
            return
        while True:
            item_retrieved = False
            try:
                track_id, token, operation_id = await self._queue.get()
                item_retrieved = True
                await self._poll_status(track_id, token, operation_id)
            except asyncio.CancelledError:
                raise
            except Exception as exc:  # pragma: no cover
                bind_request_context(job="dgii_status").error("Fallo en job DGII", error=str(exc))
            finally:
                if item_retrieved:
                    self._queue.task_done()

    async def _poll_status(self, track_id: str, token: str, operation_id: str) -> None:
        bind_request_context(job="dgii_status", track_id=track_id, operation_id=operation_id)
        async with DGIIClient(config=self.config) as client:
            result = await client.get_status(track_id, token)
        await asyncio.to_thread(_persist_status_and_sync, operation_id, track_id, result)


dispatcher = DGIIJobDispatcher()


def _persist_status_and_sync(operation_id: str, track_id: str, result: dict) -> None:
    with session_scope() as session:
        operation = session.scalar(select(FiscalOperation).where(FiscalOperation.operation_id == operation_id))
        if operation is None:
            return
        operations = FiscalOperationService(session)
        operations.transition(
            operation,
            state="QUERYING_TRACK_STATUS",
            title="Consultando TrackId DGII",
            message=track_id,
            stage="QUERYING_TRACK_STATUS",
            details=result,
        )
        raw_status = str(result.get("estado") or result.get("status") or "")
        normalized_state = map_remote_status(raw_status)
        operation.dgii_track_id = track_id
        operation.dgii_status = raw_status
        operations.update_remote_status(operation, raw_status, message=str(result.get("descripcion") or result.get("detalle") or raw_status))

        invoices = session.scalars(select(Invoice).where(Invoice.track_id == track_id)).all()
        for invoice in invoices:
            invoice.estado_dgii = raw_status or normalized_state
            invoice.track_id = track_id
            invoice.last_operation_id = operation.id
        session.flush()

        if normalized_state in {"ACCEPTED", "ACCEPTED_CONDITIONAL"} and operation.invoice is not None:
            # Fix: asyncio.run() inside a thread that may already have an event loop
            # is unsafe. Use a dedicated new event loop for the sync call instead.
            loop = asyncio.new_event_loop()
            try:
                sync_result = loop.run_until_complete(
                    OdooAccountingSyncService(session).sync_operation(operation)
                )
            finally:
                loop.close()
            if sync_result.get("status") == "SYNCED_TO_ODOO":
                if normalized_state != operation.state:
                    operations.update_remote_status(operation, raw_status or normalized_state)
        elif normalized_state == "REJECTED":
            operation.odoo_sync_state = "SKIPPED"
            session.flush()


async def start_dispatcher() -> None:
    await dispatcher.start()


async def stop_dispatcher() -> None:
    await dispatcher.stop()
