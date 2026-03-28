"""add user ai providers

Revision ID: 20260327_0005
Revises: 20260327_0004
Create Date: 2026-03-27
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260327_0005"
down_revision = "20260327_0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "user_ai_providers",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
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
    op.create_index("ix_user_ai_providers_user_id", "user_ai_providers", ["user_id"], unique=False)
    op.create_index("ix_user_ai_providers_display_name", "user_ai_providers", ["display_name"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_user_ai_providers_display_name", table_name="user_ai_providers")
    op.drop_index("ix_user_ai_providers_user_id", table_name="user_ai_providers")
    op.drop_table("user_ai_providers")
