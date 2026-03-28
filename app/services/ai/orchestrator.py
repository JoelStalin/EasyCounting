"""Main AI Orchestrator."""
from __future__ import annotations

import time
from typing import Any
from sqlalchemy.orm import Session

from app.services.ai.providers.selector import ProviderSelector
from app.services.ai.conversation_service import ConversationService
from app.services.ai.memory_service import MemoryService
from app.services.ai.context_builder import ContextBuilder


class ChatOrchestrator:
    """Orquesta el flujo completo de una consulta de IA."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.provider_selector = ProviderSelector(db)
        self.conversation_service = ConversationService(db)
        self.memory_service = MemoryService(db)
        self.context_builder = ContextBuilder(db, self.memory_service)

    async def answer(
        self, 
        tenant_id: int, 
        user_id: int | None, 
        question: str, 
        session_id: int | None = None
    ) -> dict[str, Any]:
        # 1. Obtener o crear sesión
        if session_id:
            session = self.conversation_service.get_session(session_id, tenant_id)
            if not session:
                session = self.conversation_service.get_or_create_session(tenant_id, user_id)
        else:
            session = self.conversation_service.get_or_create_session(tenant_id, user_id)

        # 2. Construir historial
        history = self.conversation_service.get_history(session.id, limit=10)
        
        # 3. Construir contexto (RAG)
        context = await self.context_builder.build_context(tenant_id, question)
        
        # 4. Seleccionar proveedor
        provider = self.provider_selector.get_provider(tenant_id, user_id)
        
        # 5. Preparar prompt
        system_prompt = (
            "Eres un asistente experto en contabilidad fiscal de República Dominicana para la plataforma EasyCounting. "
            "Responde de forma profesional y concisa basándote en el contexto proporcionado. "
            f"\n\nContexto actual:\n{context}"
        )
        
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(history)
        messages.append({"role": "user", "content": question})

        # 6. Ejecutar consulta
        response = await provider.chat(messages)

        # 7. Persistir mensajes
        self.conversation_service.add_message(session.id, "user", question)
        bot_msg = self.conversation_service.add_message(
            session.id, 
            "assistant", 
            response.content,
            provider=response.provider,
            model=response.model,
            usage=response.usage,
            latency_ms=response.latency_ms
        )

        return {
            "answer": response.content,
            "session_id": session.id,
            "engine": response.model,
            "provider": response.provider,
            "latency_ms": response.latency_ms,
            "usage": response.usage
        }
