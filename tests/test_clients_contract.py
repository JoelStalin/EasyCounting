from __future__ import annotations

from pathlib import Path

import httpx
import pytest
import respx

from app.core.config import settings
from app.dgii.client import DGIIClient
from app.dgii.signing import sign_ecf


@pytest.mark.asyncio
@respx.mock
async def test_dgii_client_flow_with_retries(configured_settings) -> None:
    auth_base = str(settings.url_for("auth"))
    recepcion_base = str(settings.url_for("recepcion"))

    respx.get(f"{auth_base}/semilla").respond(200, content=b"<Autenticacion><Semilla>ABC123</Semilla></Autenticacion>")
    respx.post(f"{auth_base}/token").respond(200, json={"access_token": "token-123", "expires_at": "2024-05-01T00:00:00Z"})

    send_route = respx.post(f"{recepcion_base}/ecf").mock(
        side_effect=[
            httpx.Response(500),
            httpx.Response(202, json={"trackId": "TRACK-123", "estado": "EN_PROCESO"}),
        ]
    )

    status_route = respx.get(f"{recepcion_base}/estatus/TRACK-123").respond(200, json={"estado": "ACEPTADO", "descripcion": "Procesado"})

    respx.post(f"{str(settings.url_for('recepcion_fc'))}/rfce").respond(202, json={"codigo": "00", "estado": "RECIBIDO"})
    respx.post(f"{recepcion_base}/anecf").respond(202, json={"trackId": "TRACK-ANU", "estado": "RECIBIDO"})
    respx.post(f"{recepcion_base}/acecf").respond(202, json={"trackId": "TRACK-ACE", "estado": "RECIBIDO"})
    respx.post(f"{recepcion_base}/arecef").respond(202, json={"trackId": "TRACK-AR", "estado": "RECIBIDO"})

    sample_xml = Path("samples/ecf_valid.xml").read_bytes()
    signed_xml = sign_ecf(sample_xml, str(configured_settings["path"]), configured_settings["password"].decode())
    rfce_xml = sign_ecf(Path("samples/rfce_valid.xml").read_bytes(), str(configured_settings["path"]), configured_settings["password"].decode())
    anecf_xml = sign_ecf(Path("samples/anecf_valid.xml").read_bytes(), str(configured_settings["path"]), configured_settings["password"].decode())
    acecf_xml = sign_ecf(Path("samples/acecf_valid.xml").read_bytes(), str(configured_settings["path"]), configured_settings["password"].decode())
    arecf_xml = sign_ecf(Path("samples/arecf_valid.xml").read_bytes(), str(configured_settings["path"]), configured_settings["password"].decode())

    async with DGIIClient() as client:
        seed = await client.get_seed()
        signed_seed = client.sign_seed(seed)
        token_payload = await client.get_token(signed_seed)
        result = await client.send_ecf(signed_xml, token=token_payload["access_token"])
        assert result["trackId"] == "TRACK-123"
        assert result["estado"] == "EN_PROCESO"

        rfce_response = await client.send_rfce(rfce_xml, token=token_payload["access_token"])
        assert rfce_response["codigo"] == "00"

        await client.send_anecf(anecf_xml, token=token_payload["access_token"])
        await client.send_acecf(acecf_xml, token=token_payload["access_token"])
        await client.send_arecf(arecf_xml, token=token_payload["access_token"])

        status = await client.get_status("TRACK-123", token_payload["access_token"])
        assert status["estado"] == "ACEPTADO"
        assert status_route.called

    assert len(send_route.calls) == 2
    idempotency_header = send_route.calls[1].request.headers.get("Idempotency-Key")
    assert idempotency_header is not None


