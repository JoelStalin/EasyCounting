"""Application lifecycle helpers (startup/shutdown orchestration)."""
from __future__ import annotations

import logging

from fastapi import FastAPI

from app.infra.settings import settings

LOGGER = logging.getLogger(__name__)


async def startup_runtime_dependencies(app: FastAPI) -> None:
    """Initialize runtime dependencies required at startup."""

    try:
        if settings.is_production:
            from app.security.rate_limit import init_rate_limiter

            await init_rate_limiter(app, settings.redis_url)
    except Exception as exc:  # pragma: no cover - fail fast in production
        LOGGER.exception("Failed to initialise rate limiter", extra={"redis_url": settings.redis_url})
        if settings.is_production:
            raise RuntimeError("Redis connection failed during startup") from exc


async def startup_background_jobs() -> None:
    """Start optional background jobs used by the platform."""

    if not settings.jobs_enabled:
        return

    try:
        from app.dgii.jobs import start_dispatcher

        await start_dispatcher()
    except Exception as exc:  # pragma: no cover - defensive
        LOGGER.exception("Failed to start DGII dispatcher", exc_info=exc)

    try:
        from app.jobs.recurring_invoices import start_recurring_invoice_runner

        await start_recurring_invoice_runner()
    except Exception as exc:  # pragma: no cover - defensive
        LOGGER.exception("Failed to start recurring invoice runner", exc_info=exc)

    try:
        from app.jobs.certificate_workflow import start_certificate_workflow_runner

        await start_certificate_workflow_runner()
    except Exception as exc:  # pragma: no cover - defensive
        LOGGER.exception("Failed to start certificate workflow runner", exc_info=exc)


async def shutdown_runtime_dependencies(app: FastAPI) -> None:
    """Shutdown runtime dependencies gracefully."""

    from app.security.rate_limit import shutdown_rate_limiter

    await shutdown_rate_limiter(app)


async def shutdown_background_jobs() -> None:
    """Stop background jobs gracefully."""

    try:
        from app.dgii.jobs import stop_dispatcher

        await stop_dispatcher()
    except Exception as exc:  # pragma: no cover - defensive
        LOGGER.exception("Failed to stop DGII dispatcher", exc_info=exc)

    try:
        from app.jobs.recurring_invoices import stop_recurring_invoice_runner

        await stop_recurring_invoice_runner()
    except Exception as exc:  # pragma: no cover - defensive
        LOGGER.exception("Failed to stop recurring invoice runner", exc_info=exc)

    try:
        from app.jobs.certificate_workflow import stop_certificate_workflow_runner

        await stop_certificate_workflow_runner()
    except Exception as exc:  # pragma: no cover - defensive
        LOGGER.exception("Failed to stop certificate workflow runner", exc_info=exc)
