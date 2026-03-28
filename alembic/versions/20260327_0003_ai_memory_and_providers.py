"""AI memory and providers.

Revision ID: 20260327_0003
Revises: 20260327_0002
Create Date: 2026-03-27
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect
from sqlalchemy.dialects import postgresql
from pgvector.sqlalchemy import Vector


revision = "20260327_0003"
down_revision = "20260327_0002"
branch_labels = None
depends_on = None


def _inspector():
    return inspect(op.get_bind())


def _has_table(table_name: str) -> bool:
    return table_name in _inspector().get_table_names()


def _has_index(table_name: str, index_name: str) -> bool:
    if not _has_table(table_name):
        return False
    return any(index["name"] == index_name for index in _inspector().get_indexes(table_name))


def _drop_table_if_exists(table_name: str) -> None:
    if _has_table(table_name):
        op.drop_table(table_name)


def upgrade() -> None:
    # Enable pgvector extension
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # 1. tenant_ai_providers
    if not _has_table("tenant_ai_providers"):
        op.create_table(
            "tenant_ai_providers",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
            sa.Column("display_name", sa.String(length=120), nullable=False),
            sa.Column("provider_type", sa.String(length=40), nullable=False),
            sa.Column("enabled", sa.Boolean(), server_default="true", nullable=False),
            sa.Column("is_default", sa.Boolean(), server_default="false", nullable=False),
            sa.Column("base_url", sa.String(length=255), nullable=True),
            sa.Column("model", sa.String(length=160), nullable=False),
            sa.Column("encrypted_api_key", sa.Text(), nullable=True),
            sa.Column("organization_id", sa.String(length=120), nullable=True),
            sa.Column("project_id", sa.String(length=120), nullable=True),
            sa.Column("api_version", sa.String(length=64), nullable=True),
            sa.Column("system_prompt", sa.Text(), nullable=True),
            sa.Column("extra_headers_json", sa.Text(), nullable=True),
            sa.Column("timeout_seconds", sa.Float(), server_default="30.0", nullable=False),
            sa.Column("max_completion_tokens", sa.Integer(), server_default="1000", nullable=False),
        )
        op.create_index("ix_tenant_ai_providers_tenant_id", "tenant_ai_providers", ["tenant_id"], unique=False)
        op.create_index("ix_tenant_ai_providers_display_name", "tenant_ai_providers", ["display_name"], unique=False)

    # 2. chat_sessions
    if not _has_table("chat_sessions"):
        op.create_table(
            "chat_sessions",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=True),
            sa.Column("title", sa.String(length=255), nullable=True),
            sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        )
        op.create_index("ix_chat_sessions_tenant_id", "chat_sessions", ["tenant_id"], unique=False)
        op.create_index("ix_chat_sessions_user_id", "chat_sessions", ["user_id"], unique=False)

    # 3. chat_messages
    if not _has_table("chat_messages"):
        op.create_table(
            "chat_messages",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.Column("session_id", sa.Integer(), sa.ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False),
            sa.Column("role", sa.String(length=20), nullable=False),
            sa.Column("content", sa.Text(), nullable=False),
            sa.Column("provider_used", sa.String(length=40), nullable=True),
            sa.Column("model_used", sa.String(length=160), nullable=True),
            sa.Column("tokens_input", sa.Integer(), nullable=True),
            sa.Column("tokens_output", sa.Integer(), nullable=True),
            sa.Column("latency_ms", sa.Integer(), nullable=True),
        )
        op.create_index("ix_chat_messages_session_id", "chat_messages", ["session_id"], unique=False)

    # 4. semantic_memories
    if not _has_table("semantic_memories"):
        op.create_table(
            "semantic_memories",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=True),
            sa.Column("scope", sa.String(length=40), server_default="tenant", nullable=False),
            sa.Column("memory_type", sa.String(length=40), server_default="fact", nullable=False),
            sa.Column("content", sa.Text(), nullable=False),
            sa.Column("summary", sa.String(length=255), nullable=True),
            sa.Column("embedding", Vector(1536), nullable=True),
            sa.Column("importance_score", sa.Float(), server_default="1.0", nullable=False),
            sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        )
        op.create_index("ix_semantic_memories_tenant_id", "semantic_memories", ["tenant_id"], unique=False)
        op.create_index("ix_semantic_memories_user_id", "semantic_memories", ["user_id"], unique=False)


def downgrade() -> None:
    _drop_table_if_exists("semantic_memories")
    _drop_table_if_exists("chat_messages")
    _drop_table_if_exists("chat_sessions")
    _drop_table_if_exists("tenant_ai_providers")
    # We usually don't drop the extension in downgrade to avoid breaking other things
