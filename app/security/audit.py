"""Centralized audit helpers for security decisions."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import text
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
    now = _utcnow()
    metadata_json = json.dumps(metadata, ensure_ascii=False, sort_keys=True) if metadata else None
    last_hash = db.execute(
        text("select hash_curr from audit_logs where tenant_id = :tenant_id order by id desc limit 1"),
        {"tenant_id": tenant_id},
    ).scalar_one_or_none()
    hash_prev = str(last_hash or "0" * 64)
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
    payload: dict[str, Any] = {
        "tenant_id": tenant_id,
        "actor": actor,
        "action": action,
        "resource": resource,
        "hash_prev": hash_prev,
        "hash_curr": hash_curr,
        "created_at": now,
        "updated_at": now,
    }
    column_sql = ", ".join(payload.keys())
    value_sql = ", ".join(f":{key}" for key in payload)
    db.execute(text(f"insert into audit_logs ({column_sql}) values ({value_sql})"), payload)
    record = AuditLog(
        tenant_id=tenant_id,
        actor=actor,
        action=action,
        resource=resource,
        hash_prev=hash_prev,
        hash_curr=hash_curr,
        created_at=now,
        updated_at=now,
    )
    record.actor_user_id = actor_user_id
    record.membership_id = membership_id
    record.resource_type = resource_type
    record.resource_id = resource_id
    record.decision = decision
    record.ip_address = ip_address
    record.user_agent = user_agent
    record.metadata_json = metadata_json
    return record
