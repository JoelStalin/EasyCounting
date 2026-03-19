"""Shared FastAPI dependencies for DGII routers."""
from __future__ import annotations

from typing import AsyncIterator

from fastapi import Depends, Header, HTTPException, status

from app.dgii.client import DGIIClient
from app.core.config import settings
from app.core.logging import bind_request_context


async def get_bearer_token(authorization: str = Header(...)) -> str:
    if not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authorization header inválido")
    token = authorization.split(" ", 1)[1].strip()
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token no provisto")
    return token


async def get_dgii_client() -> AsyncIterator[DGIIClient]:
    client = DGIIClient()
    try:
        yield client
    finally:
        await client.close()


def bind_request_headers(
    request_id: str | None = Header(default=None, alias=settings.request_id_header)
) -> None:
    """Bind tracing information from headers if available."""

    if request_id:
        bind_request_context(request_id=request_id)


BearerToken = Depends(get_bearer_token)
DGIIClientDep = Depends(get_dgii_client)

