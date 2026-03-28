"""Semantic memory service with pgvector and safe fallback."""
from __future__ import annotations

from typing import Any

import httpx
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.infra.settings import settings
from app.models.memory import SemanticMemory


class MemoryService:
    """Manages tenant-scoped long-term semantic memory."""

    def __init__(self, db: Session) -> None:
        self.db = db

    async def get_embeddings(self, text: str) -> list[float]:
        if not settings.llm_api_base_url or not settings.llm_api_key:
            return [0.0] * 1536

        url = f"{settings.llm_api_base_url.rstrip('/')}/embeddings"
        payload = {"input": text, "model": "text-embedding-3-small"}
        headers = {"Authorization": f"Bearer {settings.llm_api_key}"}
        try:
            async with httpx.AsyncClient(timeout=settings.llm_timeout_seconds) as client:
                resp = await client.post(url, json=payload, headers=headers)
                resp.raise_for_status()
                data = resp.json()
                return data["data"][0]["embedding"]
        except Exception:
            return [0.0] * 1536

    async def add_memory(
        self,
        tenant_id: int,
        content: str,
        memory_type: str = "fact",
        **kwargs: Any,
    ) -> SemanticMemory:
        embedding = await self.get_embeddings(content)
        memory = SemanticMemory(
            tenant_id=tenant_id,
            content=content,
            memory_type=memory_type,
            embedding=embedding,
            user_id=kwargs.get("user_id"),
            scope=kwargs.get("scope", "tenant"),
            summary=kwargs.get("summary"),
            metadata_json=kwargs.get("metadata"),
        )
        self.db.add(memory)
        self.db.flush()
        return memory

    async def search(self, tenant_id: int, query: str, limit: int = 5) -> list[SemanticMemory]:
        query_embedding = await self.get_embeddings(query)
        try:
            stmt = (
                select(SemanticMemory)
                .where(SemanticMemory.tenant_id == tenant_id)
                .order_by(SemanticMemory.embedding.l2_distance(query_embedding))
                .limit(limit)
            )
            return list(self.db.scalars(stmt).all())
        except Exception:
            fallback = (
                select(SemanticMemory)
                .where(
                    SemanticMemory.tenant_id == tenant_id,
                    func.lower(SemanticMemory.content).contains((query or "").lower()),
                )
                .order_by(SemanticMemory.updated_at.desc())
                .limit(limit)
            )
            return list(self.db.scalars(fallback).all())
