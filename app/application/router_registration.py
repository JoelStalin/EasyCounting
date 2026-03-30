"""Router registration helpers for FastAPI app composition."""
from __future__ import annotations

from collections.abc import Iterable

from fastapi import APIRouter, FastAPI


RouterEntry = tuple[APIRouter, str | None]


def include_router_entries(app: FastAPI, entries: Iterable[RouterEntry], *, prefix: str) -> None:
    """Include a group of routers under a shared prefix.

    A per-entry optional tag can be provided to keep special-case tags
    without duplicating inclusion logic in ``app.main``.
    """

    for router, tag in entries:
        kwargs: dict[str, object] = {"prefix": prefix}
        if tag is not None:
            kwargs["tags"] = [tag]
        app.include_router(router, **kwargs)
