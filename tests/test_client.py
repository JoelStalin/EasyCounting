import pytest
import respx
from httpx import Response
from app.dgii.client import DGIIClient
from app.infra.settings import settings

@pytest.mark.asyncio
@respx.mock
async def test_dgii_client_get_semilla():
    """
    Tests that the DGIIClient can successfully retrieve a semilla.
    """
    auth_base = str(settings.dgii_auth_base_url)
    respx.get(f"{auth_base}/semilla").mock(return_value=Response(200, content=b"<Autenticacion><Semilla>ABC</Semilla></Autenticacion>"))

    async with DGIIClient() as client:
        seed = await client.get_seed()

    assert b"Semilla" in seed

@pytest.mark.asyncio
@respx.mock
async def test_dgii_client_get_token():
    """
    Tests that the DGIIClient can successfully retrieve a token.
    """
    auth_base = str(settings.dgii_auth_base_url)
    respx.post(f"{auth_base}/token").mock(return_value=Response(200, json={"access_token": "test-token", "expires_at": "2024-05-01T00:00:00Z"}))

    async with DGIIClient() as client:
        payload = await client.get_token(b"<SignedSeed/>")

    assert payload["access_token"] == "test-token"

@pytest.mark.asyncio
@respx.mock
async def test_dgii_client_send_ecf():
    """
    Tests that the DGIIClient can successfully send an e-CF.
    """
    recepcion_base = str(settings.dgii_recepcion_base_url)
    respx.post(f"{recepcion_base}/ecf").mock(return_value=Response(202, json={"trackId": "test-track-id", "estado": "EN_PROCESO"}))

    async with DGIIClient() as client:
        payload = await client.send_ecf(b"<ECF/>", token="test-token")

    assert payload["trackId"] == "test-track-id"

@pytest.mark.asyncio
async def test_dgii_client_send_ecf_no_token():
    """
    Tests that the DGIIClient raises an exception when trying to send an e-CF without a token.
    """
    async with DGIIClient() as client:
        with pytest.raises(Exception):
            await client.send_ecf(b"<ECF/>", token=None)
