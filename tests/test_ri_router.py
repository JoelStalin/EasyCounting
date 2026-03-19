from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


def test_ri_render_uses_real_router() -> None:
    client = TestClient(app)
    response = client.post(
        "/ri/render?formato=html",
        json={
            "encf": "E310000000001",
            "rncEmisor": "131415161",
            "razonSocialEmisor": "GetUpSoft Demo",
            "rncReceptor": "101010101",
            "razonSocialReceptor": "Cliente Demo",
            "montoTotal": "118.00",
            "items": [
                {
                    "descripcion": "Servicio demo",
                    "cantidad": "1",
                    "precioUnitario": "118.00",
                }
            ],
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert "html" in body
    assert "qr_base64" in body
    assert "Representación Impresa" in body["html"] or "Representaci" in body["html"]
