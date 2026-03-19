"""Background runner for recurring invoice schedules."""
from __future__ import annotations

import asyncio
from contextlib import suppress
import os

from app.application.recurring_invoices import run_due_recurring_invoices_batch
from app.infra.settings import settings


class RecurringInvoiceRunner:
    def __init__(self) -> None:
        self._task: asyncio.Task[None] | None = None
        self._running = False

    async def start(self) -> None:
        if (
            not settings.jobs_enabled
            or not settings.recurring_invoice_job_enabled
            or self._running
            or bool(os.environ.get("PYTEST_CURRENT_TEST"))
        ):
            return
        self._running = True
        self._task = asyncio.create_task(self._loop())

    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            with suppress(asyncio.CancelledError):
                await self._task
            self._task = None

    async def _loop(self) -> None:
        while self._running:
            try:
                await asyncio.to_thread(run_due_recurring_invoices_batch)
            except Exception:  # pragma: no cover - defensive background guard
                pass
            await asyncio.sleep(settings.recurring_invoice_poll_seconds)


runner = RecurringInvoiceRunner()


async def start_recurring_invoice_runner() -> None:
    await runner.start()


async def stop_recurring_invoice_runner() -> None:
    await runner.stop()
