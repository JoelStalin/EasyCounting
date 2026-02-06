"""Structured logging configuration for the application."""
from __future__ import annotations

import logging
import sys
from typing import Any, Dict

import structlog

from app.core.config import settings


def configure_logging() -> None:
    """Configure structlog with JSON output."""

    timestamper = structlog.processors.TimeStamper(fmt="iso")
    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        timestamper,
        structlog.processors.EventRenamer("message"),
        structlog.processors.dict_tracebacks,
    ]

    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
    )

    structlog.configure(
        processors=shared_processors
        + [
            structlog.processors.JSONRenderer(),
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def bind_request_context(**context: Any) -> structlog.stdlib.BoundLogger:
    """Bind structured context for request lifecycle logs."""

    logger = structlog.get_logger()
    structlog.contextvars.bind_contextvars(**_sanitize_context(context))
    return logger


def reset_request_context() -> None:
    """Flush context variables to avoid leaking data between requests."""

    structlog.contextvars.clear_contextvars()


def _sanitize_context(context: Dict[str, Any]) -> Dict[str, Any]:
    """Mask sensitive values before binding to logs."""

    sanitized: Dict[str, Any] = {}
    for key, value in context.items():
        if key.lower() in {"token", "password", "secret", "cert_password", "track_id", "trackid"}:
            sanitized[key] = "***"
        else:
            sanitized[key] = value
    return sanitized
