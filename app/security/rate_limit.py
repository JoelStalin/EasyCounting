"""Rate limiting setup backed by Redis."""
from __future__ import annotations

from typing import Callable

from inspect import isawaitable

try:  # pragma: no cover - fallback para entornos sin redis
    import redis.asyncio as redis  # type: ignore[import-not-found]
except ModuleNotFoundError:  # pragma: no cover
    from app.utils import redis_stub as redis

from fastapi import Depends, FastAPI, Request, Response
from fastapi.routing import APIRoute

try:  # pragma: no cover - fallback cuando fastapi-limiter no está disponible
    from fastapi_limiter import FastAPILimiter  # type: ignore[import-not-found]
    from fastapi_limiter.depends import RateLimiter  # type: ignore[import-not-found]
except ModuleNotFoundError:  # pragma: no cover
    from app.utils.fastapi_limiter_stub import FastAPILimiter, RateLimiter

RedisFactory = Callable[[str], redis.Redis]


def _default_redis_factory(url: str) -> redis.Redis:
    return redis.from_url(url, encoding="utf-8", decode_responses=True)


def configure_rate_limiter(app: FastAPI, rate_limit_per_minute: int) -> None:
    """Attach a global dependency enforcing the configured rate limit."""

    limiter = RateLimiter(times=rate_limit_per_minute, seconds=60)

    async def _maybe_rate_limit(request: Request, response: Response) -> None:
        redis_client = getattr(FastAPILimiter, "redis", None)
        if redis_client is None:
            return
        result = limiter(request, response)
        if isawaitable(result):
            await result

    dependency = Depends(_maybe_rate_limit)

    class RateLimitedRoute(APIRoute):
        def __init__(self, *args, **kwargs):
            dependencies = list(kwargs.pop("dependencies", []))
            dependencies.append(dependency)
            super().__init__(*args, dependencies=dependencies, **kwargs)

    app.router.route_class = RateLimitedRoute


async def init_rate_limiter(
    app: FastAPI,
    redis_url: str,
    redis_factory: RedisFactory | None = None,
) -> None:
    """Initialise FastAPI-Limiter redis backend."""

    factory = redis_factory or _default_redis_factory
    redis_client = factory(redis_url)
    await FastAPILimiter.init(redis_client)
    app.state.redis_rate_limiter = redis_client


async def shutdown_rate_limiter(app: FastAPI) -> None:
    """Cleanup Redis connections when the application stops."""

    redis_client = getattr(app.state, "redis_rate_limiter", None)
    if redis_client is not None:
        await redis_client.close()
    close_fn = getattr(FastAPILimiter, "close", None)
    if close_fn and getattr(FastAPILimiter, "redis", None) is not None:
        result = close_fn()
        if isawaitable(result):  # pragma: no branch - depends on library version
            await result
