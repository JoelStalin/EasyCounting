"""Authentication routes for DGII integration."""
from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends

from app.core.logging import bind_request_context
from app.dgii.client import DGIIClient
from app.dgii.schemas import TokenResponse
from app.routers.dependencies import DGIIClientDep, bind_request_headers

router = APIRouter(prefix="/dgii/auth", tags=["DGII Auth"])


@router.post("/token", response_model=TokenResponse)
async def obtain_token(
    client: DGIIClient = DGIIClientDep,
    _trace = Depends(bind_request_headers),
) -> TokenResponse:
    seed_xml = await client.get_seed()
    bind_request_context(seed="obtenida")
    signed_seed = client.sign_seed(seed_xml)
    data = await client.get_token(signed_seed)
    expires_at = _parse_datetime(data["expires_at"])
    return TokenResponse(access_token=data["access_token"], expires_at=expires_at)


def _parse_datetime(value: str) -> datetime:
    value = value.replace("Z", "+00:00")
    return datetime.fromisoformat(value)

