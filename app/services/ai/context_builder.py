"""Context builder for RAG (Retrieval Augmented Generation)."""
from __future__ import annotations

from typing import Sequence
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.invoice import Invoice
from app.models.memory import SemanticMemory
from app.services.ai.memory_service import MemoryService
from app.infra.settings import settings


class ContextBuilder:
    """Construye el contexto para el LLM combinando facturas y memoria semántica."""

    def __init__(self, db: Session, memory_service: MemoryService) -> None:
        self.db = db
        self.memory_service = memory_service

    async def build_context(
        self, tenant_id: int, query: str, max_invoices: int = 5, max_memories: int = 3
    ) -> str:
        # 1. Recuperar y rankear facturas (Lógica tradicional)
        invoices = self._load_recent_invoices(tenant_id)
        ranked_invoices = self._rank_invoices(query, invoices)[:max_invoices]
        
        # 2. Recuperar memorias semánticas
        memories = await self.memory_service.search(tenant_id, query, limit=max_memories)
        
        # 3. Formatear contexto
        context_parts = []
        
        if ranked_invoices:
            context_parts.append("### Facturas/e-CFs Recientes:")
            for ri in ranked_invoices:
                inv = ri
                context_parts.append(
                    f"- eNCF: {inv.encf}, Emisor: {inv.issuer_tax_id or 'N/A'}, "
                    f"Receptor: {inv.rnc_receptor or 'N/A'}, Total: {inv.total}, "
                    f"Fecha: {inv.fecha_emision}, Estado: {inv.estado_dgii}"
                )
        
        if memories:
            context_parts.append("\n### Conocimiento/Memoria de Largo Plazo:")
            for mem in memories:
                context_parts.append(f"- {mem.content}")

        return "\n".join(context_parts)

    def _load_recent_invoices(self, tenant_id: int) -> list[Invoice]:
        stmt = (
            select(Invoice)
            .where(Invoice.tenant_id == tenant_id)
            .order_by(Invoice.fecha_emision.desc())
            .limit(settings.llm_max_context_invoices)
        )
        return list(self.db.scalars(stmt).all())

    def _rank_invoices(self, query: str, invoices: Sequence[Invoice]) -> list[Invoice]:
        # Implementación simplificada del ranking basado en keywords
        query_upper = query.upper()
        ranked = []
        for inv in invoices:
            score = 0
            if inv.encf and inv.encf.upper() in query_upper: score += 100
            if inv.rnc_receptor and inv.rnc_receptor in query_upper: score += 50
            if score > 0:
                ranked.append((score, inv))
        
        # Si no hay matches específicos, devolver los más recientes por fecha
        if not ranked:
            return list(invoices)
            
        return [item[1] for item in sorted(ranked, key=lambda x: x[0], reverse=True)]
