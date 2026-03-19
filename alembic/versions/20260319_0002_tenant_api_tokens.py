"""Add tenant API tokens for enterprise ERP integrations.

Revision ID: 20260319_0002
Revises: 20260319_0001
Create Date: 2026-03-19
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260319_0002"
down_revision = "20260319_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "tenant_api_tokens",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("created_by_user_id", sa.Integer(), nullable=True),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("token_prefix", sa.String(length=32), nullable=False),
        sa.Column("token_hash", sa.String(length=128), nullable=False),
        sa.Column("scopes", sa.Text(), nullable=False, server_default="invoices:read"),
        sa.Column("last_used_at", sa.DateTime(), nullable=True),
        sa.Column("expires_at", sa.DateTime(), nullable=True),
        sa.Column("revoked_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_tenant_api_tokens_tenant_id", "tenant_api_tokens", ["tenant_id"], unique=False)
    op.create_index("ix_tenant_api_tokens_token_hash", "tenant_api_tokens", ["token_hash"], unique=True)
    op.create_index("ix_tenant_api_tokens_revoked_at", "tenant_api_tokens", ["revoked_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_tenant_api_tokens_revoked_at", table_name="tenant_api_tokens")
    op.drop_index("ix_tenant_api_tokens_token_hash", table_name="tenant_api_tokens")
    op.drop_index("ix_tenant_api_tokens_tenant_id", table_name="tenant_api_tokens")
    op.drop_table("tenant_api_tokens")
