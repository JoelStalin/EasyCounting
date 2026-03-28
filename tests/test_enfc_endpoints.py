# FILE: tests/test_enfc_endpoints.py
"""Integration tests for ENFC FastAPI endpoints."""
from __future__ import annotations

import asyncio
import base64
from datetime import datetime
from pathlib import Path
from xml.etree import ElementTree as ET

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.security.xml import validate_with_xsd
from app.services.idempotency import idempotency_store

ECF_SAMPLE = Path("tests/assets/sample_ecf_32.xml").read_bytes()
APROBACION_SAMPLE_PATH = Path("tests/assets/sample_acecf.xml")
APROBACION_SAMPLE = (
    APROBACION_SAMPLE_PATH.read_bytes()
    if APROBACION_SAMPLE_PATH.exists()
    else b"<ACECF><ENCF>E310000000000</ENCF><RNCEmisor>101010101</RNCEmisor><RNCComprador>102030405</RNCComprador><Estado>ACEPTADO</Estado><Motivo>OK</Motivo><FechaAprobacion>2024-01-01T00:00:00Z</FechaAprobacion></ACECF>"
)
EXPIRED_CERT_PEM = Path("tests/assets/certs/expired.pem").read_bytes()


def _build_client() -> AsyncClient:
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")

@pytest.fixture(autouse=True)
async def _clear_idempotency():
    await idempotency_store.clear()
    yield
    await idempotency_store.clear()


@pytest.mark.asyncio
async def test_semilla_returns_seed():
    async with _build_client() as client:
        response = await client.get("/fe/autenticacion/api/semilla", headers={"Accept": "application/json"})
    data = response.json()
    assert response.status_code == 200
    assert "valor" in data
    assert "fecha" in data
    assert data["expiraEn"] == 300


@pytest.mark.asyncio
async def test_semilla_returns_xml_contract():
    async with _build_client() as client:
        response = await client.get("/fe/autenticacion/api/semilla", headers={"Accept": "application/xml"})

    assert response.status_code == 200
    assert response.headers.get("content-type", "").startswith("application/xml")
    root = ET.fromstring(response.content)
    assert root.tag == "SemillaModel"
    valor = (root.findtext("valor") or "").strip()
    fecha = (root.findtext("fecha") or "").strip()
    assert valor
    decoded = base64.b64decode(valor).decode("utf-8")
    assert ":" in decoded
    parsed_fecha = datetime.fromisoformat(fecha)
    assert parsed_fecha.tzinfo is not None


@pytest.mark.asyncio
async def test_signed_semilla_payload_validates_with_xsd():
    async with _build_client() as client:
        response = await client.get("/fe/autenticacion/api/semilla", headers={"Accept": "application/xml"})

    assert response.status_code == 200
    semilla_root = ET.fromstring(response.content)
    valor = (semilla_root.findtext("valor") or "").strip()
    fecha = (semilla_root.findtext("fecha") or "").strip()
    signed_payload = (
        '<?xml version="1.0" encoding="utf-8"?>'
        '<SemillaModel xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
        'xmlns:xsd="http://www.w3.org/2001/XMLSchema">'
        f"<valor>{valor}</valor>"
        f"<fecha>{fecha}</fecha>"
        "<Signature><SignedInfo/></Signature>"
        "</SemillaModel>"
    ).encode("utf-8")
    validate_with_xsd(signed_payload, "xsd/Semilla v.1.0.xsd")


@pytest.mark.asyncio
async def test_validacion_semilla_xml_returns_token_xml(monkeypatch):
    monkeypatch.setattr("app.api.enfc_routes.verify_xml_signature_details", lambda *_args, **_kwargs: None)
    monkeypatch.setattr("app.api.enfc_routes.validate_with_xsd", lambda *_args, **_kwargs: None)

    async with _build_client() as client:
        semilla_res = await client.get("/fe/autenticacion/api/semilla", headers={"Accept": "application/xml"})
        semilla_root = ET.fromstring(semilla_res.content)
        valor = (semilla_root.findtext("valor") or "").strip()
        fecha = (semilla_root.findtext("fecha") or "").strip()
        body = (
            '<?xml version="1.0" encoding="utf-8"?>'
            '<SemillaModel xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
            'xmlns:xsd="http://www.w3.org/2001/XMLSchema">'
            f"<valor>{valor}</valor><fecha>{fecha}</fecha></SemillaModel>"
        )
        token_res = await client.post(
            "/fe/autenticacion/api/validacioncertificado",
            content=body.encode("utf-8"),
            headers={"Content-Type": "text/xml", "Accept": "application/xml"},
        )

    assert token_res.status_code == 200
    token_root = ET.fromstring(token_res.content)
    assert token_root.tag == "RespuestaAutenticacion"
    assert (token_root.findtext("token") or "").strip()
    assert (token_root.findtext("expira") or "").strip()
    assert (token_root.findtext("expedido") or "").strip()


@pytest.mark.asyncio
async def test_validacion_certificado_input_vacio():
    async with _build_client() as client:
        response = await client.post(
            "/fe/autenticacion/api/validacioncertificado",
            headers={"Accept": "application/json"},
            json={},
        )
    assert response.status_code == 200
    assert response.json()["valido"] is False


@pytest.mark.asyncio
async def test_validacion_certificado_expired():
    async with _build_client() as client:
        response = await client.post(
            "/fe/autenticacion/api/validacioncertificado",
            headers={"Accept": "application/json"},
            json={"cert_b64": base64.b64encode(EXPIRED_CERT_PEM).decode()},
        )
    assert response.status_code == 200
    assert response.json()["valido"] is False
    assert "Certificado vencido" in response.json()["detalle"]


@pytest.mark.asyncio
async def test_recepcion_ecf_no_idempotency_header(monkeypatch):
    payload = {
        "formato": "XML",
        "ecf_xml_b64": base64.b64encode(ECF_SAMPLE).decode(),
    }
    monkeypatch.setattr("app.services.recepcion_service.verify_xml_signature", lambda _xml: True)
    monkeypatch.setattr("app.services.recepcion_service.validate_with_xsd", lambda *_args, **_kwargs: None)
    async with _build_client() as client:
        response = await client.post("/fe/recepcion/api/ecf", json=payload, headers={"Accept": "application/json"})
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_recepcion_ecf_success(monkeypatch):
    monkeypatch.setattr("app.services.recepcion_service.verify_xml_signature", lambda _xml: True)
    monkeypatch.setattr("app.services.recepcion_service.validate_with_xsd", lambda *_args, **_kwargs: None)
    payload = {
        "formato": "XML",
        "ecf_xml_b64": base64.b64encode(ECF_SAMPLE).decode(),
    }
    headers = {"Idempotency-Key": "abc123", "Accept": "application/json"}
    async with _build_client() as client:
        response = await client.post(
            "/fe/recepcion/api/ecf",
            json=payload,
            headers=headers,
        )
        replay = await client.post(
            "/fe/recepcion/api/ecf",
            json=payload,
            headers=headers,
        )
    assert response.status_code == 200
    data = response.json()
    assert data["estado"] == "RECIBIDO"
    assert replay.headers.get("Idempotent-Replay") == "true"
    assert replay.json() == data


@pytest.mark.asyncio
async def test_recepcion_ecf_invalid_signature(monkeypatch):
    monkeypatch.setattr("app.services.recepcion_service.verify_xml_signature", lambda _xml: False)
    monkeypatch.setattr("app.services.recepcion_service.validate_with_xsd", lambda *_args, **_kwargs: None)
    payload = {
        "formato": "XML",
        "ecf_xml_b64": base64.b64encode(ECF_SAMPLE).decode(),
    }
    headers = {"Idempotency-Key": "key-invalid", "Accept": "application/json"}
    async with _build_client() as client:
        response = await client.post(
            "/fe/recepcion/api/ecf",
            json=payload,
            headers=headers,
        )
    assert response.status_code == 400
    assert "Firma inválida" in response.json()["detail"]


@pytest.mark.asyncio
async def test_aprobacion_ecf_success(monkeypatch):
    monkeypatch.setattr("app.services.aprobacion_service.validate_with_xsd", lambda *_args, **_kwargs: None)
    monkeypatch.setattr("app.services.aprobacion_service.verify_xml_signature", lambda _xml: True)
    payload = {
        "aprobacion_xml_b64": base64.b64encode(APROBACION_SAMPLE).decode(),
    }
    headers = {"Idempotency-Key": "approv-1", "Accept": "application/json"}
    async with _build_client() as client:
        response = await client.post(
            "/fe/aprobacioncomercial/api/ecf",
            json=payload,
            headers=headers,
        )
    assert response.status_code == 200
    assert response.json()["estado"] == "ACEPTADO"


@pytest.mark.asyncio
async def test_aprobacion_content_type_invalido():
    headers = {
        "Idempotency-Key": "approv-2",
        "Accept": "application/json",
        "Content-Type": "text/plain",
    }
    async with _build_client() as client:
        response = await client.post(
            "/fe/aprobacioncomercial/api/ecf",
            content="hola",
            headers=headers,
        )
    assert response.status_code == 415


@pytest.mark.asyncio
async def test_recepcion_multipart_xml(monkeypatch):
    monkeypatch.setattr("app.services.recepcion_service.verify_xml_signature", lambda _xml: True)
    monkeypatch.setattr("app.services.recepcion_service.validate_with_xsd", lambda *_args, **_kwargs: None)
    async with _build_client() as client:
        response = await client.post(
            "/fe/recepcion/api/ecf",
            files={"xml": ("ecf.xml", ECF_SAMPLE, "text/xml")},
            headers={"Accept": "application/json"},
        )
    assert response.status_code == 200
    assert response.json()["estado"] == "RECIBIDO"
