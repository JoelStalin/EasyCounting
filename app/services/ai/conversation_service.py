"""Conversation management service."""
from __future__ import annotations

from datetime import datetime
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.memory import ChatSession, ChatMessage


class ConversationService:
    """Gestiona sesiones y mensajes de chat persistentes."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_or_create_session(
        self, tenant_id: int, user_id: int | None, title: str | None = None
    ) -> ChatSession:
        # Intentar obtener la última sesión abierta si no se especifica título (o lógica similar)
        # Para simplificar, siempre creamos una nueva si el usuario lo pide, o recuperamos por ID.
        session = ChatSession(
            tenant_id=tenant_id,
            user_id=user_id,
            title=title or f"Chat {datetime.now():%Y-%m-%d %H:%M}",
        )
        self.db.add(session)
        self.db.flush()
        return session

    def get_session(self, session_id: int, tenant_id: int) -> ChatSession | None:
        return self.db.scalar(
            select(ChatSession).where(ChatSession.id == session_id, ChatSession.tenant_id == tenant_id)
        )

    def list_sessions(self, tenant_id: int, user_id: int | None = None) -> list[ChatSession]:
        stmt = select(ChatSession).where(ChatSession.tenant_id == tenant_id).order_by(ChatSession.updated_at.desc())
        if user_id:
            stmt = stmt.where(ChatSession.user_id == user_id)
        return list(self.db.scalars(stmt).all())

    def add_message(
        self,
        session_id: int,
        role: str,
        content: str,
        provider: str | None = None,
        model: str | None = None,
        usage: dict[str, int] | None = None,
        latency_ms: int | None = None,
    ) -> ChatMessage:
        msg = ChatMessage(
            session_id=session_id,
            role=role,
            content=content,
            provider_used=provider,
            model_used=model,
            tokens_input=usage.get("input_tokens") if usage else None,
            tokens_output=usage.get("output_tokens") if usage else None,
            latency_ms=latency_ms,
        )
        self.db.add(msg)
        
        # Actualizar timestamp de la sesión
        session = self.db.get(ChatSession, session_id)
        if session:
            session.updated_at = datetime.now()
            
        self.db.flush()
        return msg

    def get_history(self, session_id: int, limit: int = 20) -> list[dict[str, str]]:
        stmt = (
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at.desc())
            .limit(limit)
        )
        messages = list(self.db.scalars(stmt).all())
        # Devolver en orden cronológico para el LLM
        return [{"role": m.role, "content": m.content} for m in reversed(messages)]
