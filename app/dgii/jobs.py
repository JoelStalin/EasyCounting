"""Simple background dispatcher for DGII follow-up jobs."""
from __future__ import annotations

import asyncio
from contextlib import suppress
from typing import Tuple

from sqlalchemy import select

from app.core.config import Settings, settings
from app.core.logging import bind_request_context
from app.dgii.clients import DGIIClient
from app.models.invoice import Invoice
from app.shared.database import session_scope


class DGIIJobDispatcher:
    def __init__(self, config: Settings | None = None) -> None:
        self.config = config or settings
        self._queue: asyncio.Queue[Tuple[str, str]] = asyncio.Queue()
        self._worker: asyncio.Task[None] | None = None
        self._running = False

    async def start(self) -> None:
        if not self.config.jobs_enabled or self._running:
            return
        self._running = True
        self._worker = asyncio.create_task(self._consume())

    async def stop(self) -> None:
        self._running = False
        if self._worker:
            self._worker.cancel()
            with suppress(asyncio.CancelledError):
                await self._worker
            self._worker = None
        while not self._queue.empty():
            try:
                self._queue.get_nowait()
                self._queue.task_done()
            except asyncio.QueueEmpty:  # pragma: no cover - race guard
                break

    async def enqueue_status_check(self, track_id: str, token: str) -> None:
        if not self.config.jobs_enabled:
            return
        await self._queue.put((track_id, token))

    async def _consume(self) -> None:
        while True:
            try:
                track_id, token = await self._queue.get()
                await self._poll_status(track_id, token)
            except asyncio.CancelledError:
                raise
            except Exception as exc:  # pragma: no cover - defensive logging
                bind_request_context(job="dgii_status").error("Fallo en job DGII", error=str(exc))
            finally:
                self._queue.task_done()

    async def _poll_status(self, track_id: str, token: str) -> None:
        bind_request_context(job="dgii_status", track_id=track_id)
        async with DGIIClient(config=self.config) as client:
            result = await client.get_status(track_id, token)
            estado = result.get("estado") or result.get("status")
            bind_request_context(estado=estado or "desconocido").info("Estado DGII consultado")
            if estado:
                await asyncio.to_thread(_persist_invoice_status, track_id, str(estado))


dispatcher = DGIIJobDispatcher()


def _persist_invoice_status(track_id: str, estado: str) -> None:
    with session_scope() as session:
        invoices = session.scalars(select(Invoice).where(Invoice.track_id == track_id)).all()
        if not invoices:
            return
        for invoice in invoices:
            invoice.estado_dgii = estado
        session.flush()


async def start_dispatcher() -> None:
    await dispatcher.start()


async def stop_dispatcher() -> None:
    await dispatcher.stop()
