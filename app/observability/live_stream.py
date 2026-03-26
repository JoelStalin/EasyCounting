"""SSE helpers backed by persisted fiscal operation events."""
from __future__ import annotations

import asyncio
import json
from typing import Any, AsyncIterator

from fastapi import Request
from sqlalchemy import select

from app.models.fiscal_operation import FiscalOperation, FiscalOperationEvent
from app.shared.database import session_scope


def _format_sse(data: dict[str, Any], *, event: str = "message", event_id: int | None = None) -> str:
    chunks = []
    if event_id is not None:
        chunks.append(f"id: {event_id}")
    chunks.append(f"event: {event}")
    chunks.append(f"data: {json.dumps(data, ensure_ascii=True, default=str)}")
    return "\n".join(chunks) + "\n\n"


def _load_events_after(operation_id: str, last_seen_id: int) -> list[dict[str, Any]]:
    with session_scope() as session:
        operation_pk = session.scalar(select(FiscalOperation.id).where(FiscalOperation.operation_id == operation_id))
        if operation_pk is None:
            return []
        rows = session.scalars(
            select(FiscalOperationEvent)
            .where(
                FiscalOperationEvent.operation_fk == operation_pk,
                FiscalOperationEvent.id > last_seen_id,
            )
            .order_by(FiscalOperationEvent.id.asc())
        ).all()
        return [
            {
                "id": row.id,
                "status": row.status,
                "title": row.title,
                "message": row.message,
                "stage": row.stage,
                "duration_ms": row.duration_ms,
                "details_json": row.details_json or {},
                "occurred_at": row.occurred_at.isoformat(),
            }
            for row in rows
        ]


async def stream_operation_events(operation_id: str, request: Request) -> AsyncIterator[str]:
    """Yield persisted operation events as SSE."""

    accept_header = request.headers.get("accept", "")
    tail_stream = "text/event-stream" in accept_header.lower()
    last_seen_id = 0
    yield ": stream-open\n\n"
    while not await request.is_disconnected():
        events = await asyncio.to_thread(_load_events_after, operation_id, last_seen_id)
        if events:
            for event in events:
                if await request.is_disconnected():
                    break
                last_seen_id = max(last_seen_id, int(event["id"]))
                yield _format_sse(event, event="operation_event", event_id=int(event["id"]))
            if not tail_stream:
                return
            continue
        if not tail_stream:
            yield ": keep-alive\n\n"
            return
        yield ": keep-alive\n\n"
        await asyncio.sleep(0.5)
