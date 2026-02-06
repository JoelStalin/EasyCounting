"""Pruebas integradas básicas."""
from __future__ import annotations

import base64

from fastapi.testclient import TestClient

from app.main import app


def test_healthz() -> None:
    with TestClient(app) as client:
        response = client.get("/healthz")
        assert response.status_code == 200


def test_sign_and_dgii_flow() -> None:
    xml = base64.b64encode(b"<Factura><Total>1</Total></Factura>").decode()
    with TestClient(app) as client:
        sign_resp = client.post("/api/1/sign/xml", json={"xml": xml, "certificate_subject": "CN=Demo"})
        assert sign_resp.status_code == 200
        codigo = sign_resp.json()["codigo_seguridad"]
        assert len(codigo) == 6
