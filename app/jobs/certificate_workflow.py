"""Background runner for certificate workflow reminders."""
from __future__ import annotations

import asyncio
from contextlib import suppress
import os

from app.certificate_workflow.reminder_service import process_due_reminders
from app.certificate_workflow.track_polling_service import process_ready_cases_track_poll_from_settings
from app.infra.settings import settings


class CertificateWorkflowReminderRunner:
    def __init__(self) -> None:
        self._task: asyncio.Task[None] | None = None
        self._running = False

    async def start(self) -> None:
        if (
            not settings.jobs_enabled
            or not settings.certificate_workflow_reminder_job_enabled
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
                await asyncio.to_thread(process_due_reminders)
            except Exception:
                pass
            try:
                await process_ready_cases_track_poll_from_settings()
            except Exception:
                pass
            await asyncio.sleep(settings.certificate_workflow_reminder_poll_seconds)


runner = CertificateWorkflowReminderRunner()


async def start_certificate_workflow_runner() -> None:
    await runner.start()


async def stop_certificate_workflow_runner() -> None:
    await runner.stop()
