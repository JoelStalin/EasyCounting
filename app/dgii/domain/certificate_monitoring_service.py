from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.dgii.domain.certificate_provider import CertificateMetadata


class CertificateMonitoringService:
    """Evaluate certificate expiration windows for operational alerting."""

    def should_alert_expiration(self, metadata: CertificateMetadata, alert_days: int) -> bool:
        now = datetime.now(timezone.utc)
        return metadata.not_after <= now + timedelta(days=alert_days)
