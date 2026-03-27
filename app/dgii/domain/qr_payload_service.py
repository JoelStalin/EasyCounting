from __future__ import annotations

from urllib.parse import urlencode


class QrPayloadService:
    """Build QR payload using persisted invoice and DGII tracking data."""

    def build_qr_payload(self, invoice_data: dict, track_status: dict) -> str:
        params = {
            "encf": invoice_data.get("encf", ""),
            "rnc": invoice_data.get("rnc_emisor", ""),
            "trackId": track_status.get("track_id", ""),
            "estado": track_status.get("estado", ""),
            "monto": invoice_data.get("monto_total", ""),
        }
        return urlencode(params)
