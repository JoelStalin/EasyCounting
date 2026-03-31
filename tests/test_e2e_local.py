from __future__ import annotations

import socket
from datetime import datetime, timezone

import pytest
import respx
from fastapi.testclient import TestClient

from app.main import app


def _db_reachable() -> bool:
    """Comprueba si el hostname Docker 'db' es alcanzable (solo dentro de Docker network)."""
    try:
        socket.getaddrinfo("db", 5432, proto=socket.IPPROTO_TCP)
        return True
    except OSError:
        return False


@pytest.mark.skipif(not _db_reachable(), reason="PostgreSQL en db:5432 no alcanzable fuera de Docker network")
@respx.mock
def test_e2e_seed_token_send_ecf_status_and_ri(configured_settings) -> None:
    from app.core.config import settings

    auth_base = str(settings.url_for("auth"))
    recepcion_base = str(settings.url_for("recepcion"))

    respx.get(f"{auth_base}/semilla").respond(200, content=b"<Autenticacion><Semilla>ABC123</Semilla></Autenticacion>")
    respx.post(f"{auth_base}/token").respond(200, json={"access_token": "token-123", "expires_at": datetime.now(timezone.utc).replace(tzinfo=None).isoformat()})
    respx.post(f"{recepcion_base}/ecf").respond(202, json={"trackId": "TRACK-XYZ", "estado": "EN_PROCESO"})
    respx.get(f"{recepcion_base}/estatus/TRACK-XYZ").respond(200, json={"estado": "ACEPTADO", "descripcion": "Procesado"})

    payload = {
        "encf": "E310000000001",
        "tipoECF": "E31",
        "rncEmisor": "131415161",
        "rncReceptor": "172839405",
        "fechaEmision": datetime.now(timezone.utc).replace(tzinfo=None).isoformat(),
        "montoTotal": 1500.0,
        "moneda": "DOP",
        "items": [
            {
                "descripcion": "Servicio de consultoría",
                "cantidad": 1,
                "precioUnitario": 1500.0,
            }
        ],
    }

    ri_request = {
        "encf": "E310000000001",
        "rncEmisor": "131415161",
        "razonSocialEmisor": "Empresa Demo",
        "rncReceptor": "172839405",
        "razonSocialReceptor": "Cliente Demo",
        "montoTotal": 1500.0,
        "fechaEmision": datetime.now(timezone.utc).replace(tzinfo=None).isoformat(),
        "items": [
            {
                "descripcion": "Servicio de consultoría",
                "cantidad": 1,
                "precioUnitario": 1500.0,
            }
        ],
    }

    with TestClient(app) as client:
        token_response = client.post("/api/dgii/auth/token")
        assert token_response.status_code == 200
        token = token_response.json()["access_token"]

        headers = {"Authorization": f"Bearer {token}"}
        send_response = client.post("/api/dgii/recepcion/ecf", json=payload, headers=headers)
        assert send_response.status_code == 202
        track_id = send_response.json()["trackId"]

        status_response = client.get(f"/api/dgii/recepcion/status/{track_id}", headers=headers)
        assert status_response.status_code == 200
        assert status_response.json()["estado"] == "ACEPTADO"

        ri_response = client.post("/ri/render", json=ri_request)
        assert ri_response.status_code == 200
        body = ri_response.json()
        assert "html" in body
        assert "qr_base64" in body
