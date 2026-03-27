"""FastAPI application entrypoint."""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import Any

import sentry_sdk
from fastapi import FastAPI, Request, Response, status
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from prometheus_fastapi_instrumentator import Instrumentator
from starlette.middleware.sessions import SessionMiddleware

from app.api.routes.auth import me_router as portal_me_router
from app.api.routes.auth import router as portal_auth_router
from app.api.routes.receptor import router as receptor_router
from app.api.routes.ri import router as ri_router
from app.api.enfc_routes import router as enfc_router
from app.api.router import api_router
from app.dgii.jobs import start_dispatcher, stop_dispatcher
from app.jobs.recurring_invoices import start_recurring_invoice_runner, stop_recurring_invoice_runner
from app.jobs.certificate_workflow import start_certificate_workflow_runner, stop_certificate_workflow_runner
from app.core.logging import bind_request_context, reset_request_context
from app.routers.acuse import router as arecef_router
from app.routers.admin import router as admin_router
from app.routers.anulacion import router as anecf_router
from app.routers.aprobacion import router as acecf_router
from app.routers.auth import router as dgii_auth_router
from app.routers.cliente import router as cliente_router
from app.routers.certificate_workflow import router as certificate_workflow_router
from app.routers.dgii import router as dgii_router
from app.routers.ecf import router as ecf_router
from app.routers.internal import router as internal_router
from app.routers.odoo import router as odoo_router
from app.routers.operations import router as operations_router
from app.routers.partner import router as partner_router
from app.routers.recepcion import router as recepcion_router
from app.routers.rfce import router as rfce_router
from app.routers.tenant_api import router as tenant_api_router
from app.routers.ui_tours import router as ui_tours_router
from app.db import check_database_connection
from app.infra.logging import configure_logging
from app.infra.settings import settings
from app.security.auth import setup_security
from app.security.rate_limit import configure_rate_limiter, init_rate_limiter, shutdown_rate_limiter
from app.shared.tracing import ensure_trace_id, get_request_id

LOGGER = logging.getLogger(__name__)
INSTRUMENTATOR = Instrumentator(
    should_group_status_codes=True,
    should_ignore_untemplated=True,
    should_respect_env_var=False,
    excluded_handlers={"/livez", "/readyz"},
)

ENFC_TAG_METADATA = {
    "name": "ENFC",
    "description": "Rutas DGII ENFC para recepción y autenticación de e-CF.",
}


async def _is_redis_ready(app: FastAPI) -> bool:
    redis_client = getattr(app.state, "redis_rate_limiter", None)
    if redis_client is None:
        return settings.environment.lower() not in {"production", "prod"}
    try:
        await redis_client.ping()
        return True
    except Exception as exc:  # pragma: no cover - defensive
        LOGGER.warning(
            "Redis ping failed during readiness probe",
            extra={"redis_url": settings.redis_url},
            exc_info=exc,
        )
        return False


def create_app() -> FastAPI:
    configure_logging()

    if settings.sentry_dsn:
        sentry_sdk.init(
            dsn=settings.sentry_dsn,
            environment=settings.environment,
            traces_sample_rate=settings.sentry_traces_sample_rate,
        )

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        try:
            if settings.environment.lower() in {"production", "prod"}:
                await init_rate_limiter(app, settings.redis_url)
        except Exception as exc:  # pragma: no cover - fail fast
            LOGGER.exception("Failed to initialise rate limiter", extra={"redis_url": settings.redis_url})
            if settings.environment.lower() in {"production", "prod"}:
                raise RuntimeError("Redis connection failed during startup") from exc

        try:
            if settings.jobs_enabled:
                await start_dispatcher()
        except Exception as exc:  # pragma: no cover - defensive
            LOGGER.exception("Failed to start DGII dispatcher", exc_info=exc)

        try:
            if settings.jobs_enabled:
                await start_recurring_invoice_runner()
        except Exception as exc:  # pragma: no cover - defensive
            LOGGER.exception("Failed to start recurring invoice runner", exc_info=exc)
        try:
            if settings.jobs_enabled:
                await start_certificate_workflow_runner()
        except Exception as exc:  # pragma: no cover - defensive
            LOGGER.exception("Failed to start certificate workflow runner", exc_info=exc)

        yield

        await shutdown_rate_limiter(app)
        try:
            await stop_dispatcher()
        except Exception as exc:  # pragma: no cover - defensive
            LOGGER.exception("Failed to stop DGII dispatcher", exc_info=exc)
        try:
            await stop_recurring_invoice_runner()
        except Exception as exc:  # pragma: no cover - defensive
            LOGGER.exception("Failed to stop recurring invoice runner", exc_info=exc)
        try:
            await stop_certificate_workflow_runner()
        except Exception as exc:  # pragma: no cover - defensive
            LOGGER.exception("Failed to stop certificate workflow runner", exc_info=exc)

    app = FastAPI(
        title=settings.app_name,
        version="2.0.0",
        openapi_tags=[ENFC_TAG_METADATA],
        lifespan=lifespan,
    )

    if not getattr(app.state, "metrics_configured", False):
        INSTRUMENTATOR.instrument(app).expose(app, include_in_schema=False, endpoint="/metrics")
        app.state.metrics_configured = True

    app.add_middleware(GZipMiddleware, minimum_size=1024)
    app.add_middleware(
        SessionMiddleware,
        secret_key=settings.social_auth_session_secret,
        same_site="lax",
        https_only=settings.environment.lower() in {"production", "prod"},
    )
    trusted_hosts = sorted(
        {
            *settings.dgii_allowed_hosts,
            "localhost",
            "127.0.0.1",
            "testserver",
            "test",
            "getupsoft.com.do",
            settings.app_portal_domain,
            settings.public_site_domain,
            "api.getupsoft.com.do",
            settings.admin_portal_domain,
            settings.client_portal_domain,
            settings.partner_portal_domain,
        }
    )
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=trusted_hosts)

    setup_security(app, allowed_origins=settings.cors_allow_origins)
    if settings.environment.lower() in {"production", "prod"}:
        configure_rate_limiter(app, rate_limit_per_minute=settings.rate_limit_per_minute)

    # Portal endpoints (used by React admin/client portals)
    app.include_router(portal_auth_router, prefix="/auth", tags=["portal-auth"])
    app.include_router(portal_me_router, tags=["portal-auth"])

    # Versioned API (future stable contract)
    app.include_router(portal_auth_router, prefix="/api/v1/auth", tags=["portal-auth"])
    app.include_router(portal_me_router, prefix="/api/v1", tags=["portal-auth"])
    app.include_router(admin_router, prefix="/api/v1")
    app.include_router(cliente_router, prefix="/api/v1")
    app.include_router(internal_router, prefix="/api/v1")
    app.include_router(certificate_workflow_router, prefix="/api/v1/internal")
    app.include_router(odoo_router, prefix="/api/v1")
    app.include_router(operations_router, prefix="/api/v1")
    app.include_router(partner_router, prefix="/api/v1")
    app.include_router(tenant_api_router, prefix="/api/v1")
    app.include_router(ui_tours_router, prefix="/api/v1")
    app.include_router(dgii_auth_router, prefix="/api/v1")
    app.include_router(recepcion_router, prefix="/api/v1")
    app.include_router(rfce_router, prefix="/api/v1")
    app.include_router(anecf_router, prefix="/api/v1")
    app.include_router(acecf_router, prefix="/api/v1")
    app.include_router(arecef_router, prefix="/api/v1")
    app.include_router(dgii_router, prefix="/api/v1/dgii", tags=["dgii-scraper"])
    app.include_router(ecf_router, prefix="/api/v1/ecf", tags=["ecf-engine"])

    # Legacy paths (kept for existing tests/integrations)
    app.include_router(admin_router, prefix="/api")
    app.include_router(cliente_router, prefix="/api")
    app.include_router(internal_router, prefix="/api")
    app.include_router(certificate_workflow_router, prefix="/api/internal")
    app.include_router(odoo_router, prefix="/api")
    app.include_router(operations_router, prefix="/api")
    app.include_router(partner_router, prefix="/api")
    app.include_router(tenant_api_router, prefix="/api")
    app.include_router(ui_tours_router, prefix="/api")
    app.include_router(dgii_auth_router, prefix="/api")
    app.include_router(recepcion_router, prefix="/api")
    app.include_router(rfce_router, prefix="/api")
    app.include_router(anecf_router, prefix="/api")
    app.include_router(acecf_router, prefix="/api")
    app.include_router(arecef_router, prefix="/api")

    app.include_router(api_router, prefix="/api")
    app.include_router(api_router, prefix="/api/1")
    app.include_router(enfc_router)
    app.include_router(receptor_router, prefix="/receptor", tags=["receptor"])
    app.include_router(ri_router, prefix="/ri", tags=["ri"])

    @app.middleware("http")
    async def tracing_context(request: Request, call_next) -> Response:  # type: ignore[override]
        trace_id = ensure_trace_id(request)
        request_id = get_request_id(request)
        bind_request_context(trace_id=trace_id, request_id=request_id or "", path=request.url.path, method=request.method)
        try:
            response = await call_next(request)
        finally:
            reset_request_context()
        response.headers.setdefault(settings.tracing_header, trace_id)
        if request_id:
            response.headers.setdefault(settings.request_id_header, request_id)
        return response

    @app.middleware("http")
    async def security_headers(request: Request, call_next) -> Response:  # type: ignore[override]
        response = await call_next(request)
        response.headers.setdefault("Content-Security-Policy", "default-src 'self'")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("Referrer-Policy", "no-referrer")
        response.headers.setdefault("X-Request-ID", request.headers.get("X-Request-ID", ""))
        return response

    @app.get("/health", tags=["infra"], include_in_schema=False)
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/healthz", tags=["infra"], include_in_schema=False)
    async def healthz() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/livez", tags=["infra"], include_in_schema=False)
    async def livez() -> dict[str, str]:
        return {"status": "alive"}

    @app.get("/readyz", tags=["infra"], include_in_schema=False)
    async def readyz() -> JSONResponse:
        checks: dict[str, Any] = {
            "database": await check_database_connection(),
            "redis": await _is_redis_ready(app),
        }
        is_ready = all(checks.values())
        payload = {"status": "ready" if is_ready else "degraded", "checks": checks}
        status_code = status.HTTP_200_OK if is_ready else status.HTTP_503_SERVICE_UNAVAILABLE
        return JSONResponse(status_code=status_code, content=payload)

    return app


app = create_app()
