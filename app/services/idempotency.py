"""In-memory idempotency registry for ENFC endpoints."""
from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional

_IDEMPOTENCY_TTL_SECONDS = 24 * 60 * 60  # 24 hours


@dataclass(slots=True)
class IdempotencyRecord:
    """Stored response metadata for an idempotent request."""

    payload_hash: str
    status_code: int
    body: Any
    headers: Dict[str, str]
    expires_at: float


class IdempotencyStore:
    """Thread-safe store retaining responses for replayed requests."""

    def __init__(self) -> None:
        self._records: Dict[str, IdempotencyRecord] = {}
        self._locks: Dict[int, asyncio.Lock] = {}

    def _lock_for_loop(self) -> asyncio.Lock:
        loop = asyncio.get_running_loop()
        key = id(loop)
        lock = self._locks.get(key)
        if lock is None:
            lock = asyncio.Lock()
            self._locks[key] = lock
        return lock

    async def get(self, key: str, payload_hash: str) -> Optional[IdempotencyRecord]:
        async with self._lock_for_loop():
            record = self._records.get(key)
            if not record:
                return None
            if record.expires_at < time.time():
                self._records.pop(key, None)
                return None
            if record.payload_hash != payload_hash:
                # Payload differs; treat as conflict per idempotency spec.
                raise ValueError("Payload mismatch for supplied Idempotency-Key")
            return record

    async def set(
        self,
        key: str,
        payload_hash: str,
        status_code: int,
        body: Any,
        headers: Optional[Dict[str, str]] = None,
    ) -> None:
        async with self._lock_for_loop():
            self._records[key] = IdempotencyRecord(
                payload_hash=payload_hash,
                status_code=status_code,
                body=body,
                headers=headers or {},
                expires_at=time.time() + _IDEMPOTENCY_TTL_SECONDS,
            )

    async def clear(self) -> None:
        async with self._lock_for_loop():
            self._records.clear()


idempotency_store = IdempotencyStore()
