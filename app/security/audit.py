"""Centralized audit helpers for security decisions."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.audit import AuditLog


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def append_audit_log(
    db: Session,
    *,
    tenant_id: int,
    actor: str,
    action: str,
    resource: str,
    actor_user_id: int | None = None,
    membership_id: int | None = None,
    resource_type: str | None = None,
    resource_id: str | None = None,
    decision: str | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> AuditLog:
    last = db.scalar(select(AuditLog).where(AuditLog.tenant_id == tenant_id).order_by(AuditLog.id.desc()).limit(1))
    hash_prev = last.hash_curr if last else "0" * 64
    now = _utcnow()
    metadata_json = json.dumps(metadata, ensure_ascii=False, sort_keys=True) if metadata else None
    raw = "|".join(
        [
            str(tenant_id),
            actor,
            action,
            resource,
            hash_prev,
            decision or "",
            now.isoformat(),
        ]
    )
    hash_curr = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    record = AuditLog(
        tenant_id=tenant_id,
        actor_user_id=actor_user_id,
        membership_id=membership_id,
        actor=actor,
        action=action,
        resource=resource,
        resource_type=resource_type,
        resource_id=resource_id,
        decision=decision,
        ip_address=ip_address,
        user_agent=user_agent,
        metadata_json=metadata_json,
        hash_prev=hash_prev,
        hash_curr=hash_curr,
        created_at=now,
        updated_at=now,
    )
    db.add(record)
    db.flush()
    return record
