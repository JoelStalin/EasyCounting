"""Semantic memory models for long-term persistence."""
from __future__ import annotations

from sqlalchemy import ForeignKey, Integer, String, Text, JSON, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector

from app.models.base import Base


class SemanticMemory(Base):
    """Memoria semántica por tenant para recuperación de contexto."""

    __tablename__ = "semantic_memories"

    tenant_id: Mapped[int] = mapped_column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    
    scope: Mapped[str] = mapped_column(String(40), default="tenant")  # tenant, user, session
    memory_type: Mapped[str] = mapped_column(String(40), default="fact")  # preference, fact, summary, policy
    
    content: Mapped[str] = mapped_column(Text)
    summary: Mapped[str | None] = mapped_column(String(255))
    
    # Vector embedding using pgvector (dimension 1536 for OpenAI, adjust as needed)
    embedding: Mapped[list[float]] = mapped_column(Vector(1536), nullable=True)
    
    importance_score: Mapped[float] = mapped_column(Float, default=1.0)
    metadata_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Relationships
    tenant: Mapped["Tenant"] = relationship(back_populates="memories")
    user: Mapped["User | None"] = relationship(back_populates="memories")


class ChatSession(Base):
    """Una sesión de conversación persistente."""

    __tablename__ = "chat_sessions"

    tenant_id: Mapped[int] = mapped_column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    
    title: Mapped[str | None] = mapped_column(String(255))
    metadata_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Relationships
    tenant: Mapped["Tenant"] = relationship(back_populates="chat_sessions")
    user: Mapped["User | None"] = relationship(back_populates="ai_chat_sessions")
    messages: Mapped[list["ChatMessage"]] = relationship(back_populates="session", cascade="all, delete-orphan", order_by="ChatMessage.created_at")


class ChatMessage(Base):
    """Un mensaje individual dentro de una sesión."""

    __tablename__ = "chat_messages"

    session_id: Mapped[int] = mapped_column(Integer, ForeignKey("chat_sessions.id", ondelete="CASCADE"), index=True)
    
    role: Mapped[str] = mapped_column(String(20))  # user, assistant, system
    content: Mapped[str] = mapped_column(Text)
    
    # Metadata for transparency
    provider_used: Mapped[str | None] = mapped_column(String(40))
    model_used: Mapped[str | None] = mapped_column(String(160))
    tokens_input: Mapped[int | None] = mapped_column(Integer)
    tokens_output: Mapped[int | None] = mapped_column(Integer)
    latency_ms: Mapped[int | None] = mapped_column(Integer)

    # Relationships
    session: Mapped["ChatSession"] = relationship(back_populates="messages")
