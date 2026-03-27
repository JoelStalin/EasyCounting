from __future__ import annotations

import hashlib


class SecurityCodeService:
    """Derive deterministic security code from persisted signed payload fingerprint."""

    def derive_security_code(self, invoice_data: dict, signed_fingerprint: str) -> str:
        seed = f"{invoice_data.get('encf','')}-{invoice_data.get('rnc_emisor','')}-{signed_fingerprint}"
        digest = hashlib.sha256(seed.encode("utf-8")).hexdigest().upper()
        return digest[:6]
