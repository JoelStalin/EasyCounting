"""DGII HTTP client with signing and validation."""
from __future__ import annotations

from typing import Any, Optional

from app.infra.settings import settings
from app.security.http_client import get_json, post_multipart
from app.dgii.signing import sign_ecf


class DGIIClient:
    """Wrapper around DGII services with cached token."""

    def __init__(self, token: Optional[str] = None):
        self.token = token

    async def ensure_token(self) -> str:
        if self.token:
            return self.token

        # Official flow: Semilla -> firmar -> ValidarSemilla -> token
        seed_url = f"{settings.dgii_auth_base_url}/api/Autenticacion/Semilla"
        seed_response = await get_json(seed_url, headers={})
        seed_xml = seed_response.content
        if not seed_xml:
            raise RuntimeError("DGII semilla vacía")

        signed_seed = sign_ecf(seed_xml, settings.dgii_p12_path, settings.dgii_p12_password)
        validate_url = f"{settings.dgii_auth_base_url}/api/Autenticacion/ValidarSemilla"
        files = {"xml": ("semilla.xml", signed_seed, "application/xml")}
        response = await post_multipart(validate_url, files=files, headers={})
        data = response.json()

        token = data.get("access_token") or data.get("token")
        if not token:
            raise RuntimeError("DGII token missing from response")
        self.token = token
        return token

    async def send_document(self, xml_bytes: bytes, document_type: str) -> dict[str, Any]:
        token = await self.ensure_token()

        signed = sign_ecf(xml_bytes, settings.dgii_p12_path, settings.dgii_p12_password)
        headers = {"Authorization": f"Bearer {token}"}

        if document_type.lower() == "rfce":
            url = f"{settings.dgii_recepcion_fc_base_url}/api/recepcion/ecf"
        else:
            url = f"{settings.dgii_recepcion_base_url}/api/FacturasElectronicas"

        files = {"xml": ("document.xml", signed, "application/xml")}
        response = await post_multipart(url, files=files, headers=headers)
        return response.json()

    async def get_status(self, track_id: str) -> dict[str, Any]:
        token = await self.ensure_token()

        url = f"{settings.dgii_consulta_resultado_base_url}/api/Consultas/Estado"
        headers = {"Authorization": f"Bearer {token}"}
        response = await get_json(url, headers=headers, params={"TrackId": track_id})
        return response.json()


async def get_dgii_client() -> DGIIClient:
    return DGIIClient()
