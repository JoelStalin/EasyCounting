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

from app.api.routes.auth import me_router as portal_me_router
from app.api.routes.auth import router as portal_auth_router
from app.api.routes.receptor import router as receptor_router
from app.api.routes.ri import router as ri_router
from app.api.enfc_routes import router as enfc_router
from app.api.router import api_router
from app.dgii.jobs import start_dispatcher, stop_dispatcher
from app.routers.admin import router as admin_router
from app.routers.cliente import router as cliente_router
from app.db import check_database_connection
from app.infra.logging import configure_logging
from app.infra.settings import settings
from app.security.auth import setup_security
from app.security.rate_limit import configure_rate_limiter, init_rate_limiter, shutdown_rate_limiter

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
        return False
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
            if settings.environment.lower() in {"production", "prod"}:
                await start_dispatcher()
        except Exception as exc:  # pragma: no cover - defensive
            LOGGER.exception("Failed to start DGII dispatcher", exc_info=exc)

        yield

        await shutdown_rate_limiter(app)
        try:
            await stop_dispatcher()
        except Exception as exc:  # pragma: no cover - defensive
            LOGGER.exception("Failed to stop DGII dispatcher", exc_info=exc)

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
    trusted_hosts = sorted({*settings.dgii_allowed_hosts, "localhost", "127.0.0.1", "testserver", "test"})
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

    # Legacy paths (kept for existing tests/integrations)
    app.include_router(admin_router, prefix="/api")
    app.include_router(cliente_router, prefix="/api")

    app.include_router(api_router, prefix="/api")
    app.include_router(api_router, prefix="/api/1")
    app.include_router(enfc_router)
    app.include_router(receptor_router, prefix="/receptor", tags=["receptor"])
    app.include_router(ri_router, prefix="/ri", tags=["ri"])

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
