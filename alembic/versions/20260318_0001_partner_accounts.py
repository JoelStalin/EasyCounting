"""Add partner accounts and tenant assignments

Revision ID: 20260318_0001
Revises: 20260207_0001
Create Date: 2026-03-18
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260318_0001"
down_revision = "20260207_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "partner_accounts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("slug", sa.String(length=80), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="activo"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_partner_accounts_slug", "partner_accounts", ["slug"], unique=True)

    op.add_column("users", sa.Column("partner_account_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_users_partner_account",
        "users",
        "partner_accounts",
        ["partner_account_id"],
        ["id"],
        ondelete="SET NULL",
    )

    op.create_table(
        "partner_tenant_assignments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("partner_account_id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("can_emit", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("can_manage", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["partner_account_id"], ["partner_accounts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("partner_account_id", "tenant_id", name="ux_partner_tenant_assignment"),
    )
    op.create_index(
        "ix_partner_tenant_assignments_partner_account_id",
        "partner_tenant_assignments",
        ["partner_account_id"],
        unique=False,
    )
    op.create_index(
        "ix_partner_tenant_assignments_tenant_id",
        "partner_tenant_assignments",
        ["tenant_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_partner_tenant_assignments_tenant_id", table_name="partner_tenant_assignments")
    op.drop_index("ix_partner_tenant_assignments_partner_account_id", table_name="partner_tenant_assignments")
    op.drop_table("partner_tenant_assignments")

    op.drop_constraint("fk_users_partner_account", "users", type_="foreignkey")
    op.drop_column("users", "partner_account_id")

    op.drop_index("ix_partner_accounts_slug", table_name="partner_accounts")
    op.drop_table("partner_accounts")
