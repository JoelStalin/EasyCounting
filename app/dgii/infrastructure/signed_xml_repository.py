from __future__ import annotations

import hashlib
from pathlib import Path


class SignedXmlRepository:
    """Persist immutable signed XML files with fingerprint tracking."""

    def __init__(self, root_path: str):
        self.root = Path(root_path)
        self.root.mkdir(parents=True, exist_ok=True)

    def persist(self, encf: str, xml_signed: bytes) -> dict[str, str]:
        path = self.root / f"{encf}.xml"
        if path.exists() and path.read_bytes() != xml_signed:
            raise ValueError("Intento de mutacion detectado sobre XML firmado")
        path.write_bytes(xml_signed)
        return {
            "path": str(path),
            "fingerprint_sha256": hashlib.sha256(xml_signed).hexdigest(),
        }
