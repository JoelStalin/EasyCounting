from __future__ import annotations

from app.core.logging import _sanitize_context
from app.infra.settings import settings


def test_log_redaction_masks_sensitive_fields() -> None:
    context = {
        "token": "abc",
        "password": "secret",
        "authorization": "Bearer x",
        "track_id": "TRK123",
    }
    sanitized = _sanitize_context(context)
    if settings.log_redact_secrets:
        assert sanitized["token"] == "***"
        assert sanitized["password"] == "***"
        assert sanitized["authorization"] == "***"
    assert sanitized["track_id"] == "TRK123"
