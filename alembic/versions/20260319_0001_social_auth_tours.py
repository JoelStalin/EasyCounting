"""Add social auth, MFA challenges, tours and tenant onboarding state.

Revision ID: 20260319_0001
Revises: 20260318_0001
Create Date: 2026-03-19
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260319_0001"
down_revision = "20260318_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "tenants",
        sa.Column("onboarding_status", sa.String(length=30), nullable=False, server_default="completed"),
    )

    op.create_table(
        "user_external_identities",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("provider", sa.String(length=30), nullable=False),
        sa.Column("provider_subject", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("email_verified", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("display_name", sa.String(length=255), nullable=True),
        sa.Column("avatar_url", sa.String(length=1024), nullable=True),
        sa.Column("last_login_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("provider", "provider_subject", name="ux_user_external_provider_subject"),
    )
    op.create_index("ix_user_external_identities_user_id", "user_external_identities", ["user_id"], unique=False)
    op.create_index("ix_user_external_identities_provider", "user_external_identities", ["provider"], unique=False)

    op.create_table(
        "auth_login_challenges",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("portal", sa.String(length=20), nullable=False),
        sa.Column("provider", sa.String(length=30), nullable=False, server_default="password"),
        sa.Column("challenge_hash", sa.String(length=128), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("consumed_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_auth_login_challenges_user_id", "auth_login_challenges", ["user_id"], unique=False)
    op.create_index("ix_auth_login_challenges_portal", "auth_login_challenges", ["portal"], unique=False)
    op.create_index(
        "ix_auth_login_challenges_challenge_hash",
        "auth_login_challenges",
        ["challenge_hash"],
        unique=True,
    )
    op.create_index("ix_auth_login_challenges_expires_at", "auth_login_challenges", ["expires_at"], unique=False)

    op.create_table(
        "auth_login_tickets",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("portal", sa.String(length=20), nullable=False),
        sa.Column("ticket_hash", sa.String(length=128), nullable=False),
        sa.Column("return_to", sa.String(length=1024), nullable=True),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("consumed_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_auth_login_tickets_user_id", "auth_login_tickets", ["user_id"], unique=False)
    op.create_index("ix_auth_login_tickets_portal", "auth_login_tickets", ["portal"], unique=False)
    op.create_index("ix_auth_login_tickets_ticket_hash", "auth_login_tickets", ["ticket_hash"], unique=True)
    op.create_index("ix_auth_login_tickets_expires_at", "auth_login_tickets", ["expires_at"], unique=False)

    op.create_table(
        "user_view_tours",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("view_key", sa.String(length=120), nullable=False),
        sa.Column("tour_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"),
        sa.Column("last_step", sa.Integer(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("user_id", "view_key", name="ux_user_view_tours_user_view"),
    )
    op.create_index("ix_user_view_tours_user_id", "user_view_tours", ["user_id"], unique=False)
    op.create_index("ix_user_view_tours_view_key", "user_view_tours", ["view_key"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_user_view_tours_view_key", table_name="user_view_tours")
    op.drop_index("ix_user_view_tours_user_id", table_name="user_view_tours")
    op.drop_table("user_view_tours")

    op.drop_index("ix_auth_login_tickets_expires_at", table_name="auth_login_tickets")
    op.drop_index("ix_auth_login_tickets_ticket_hash", table_name="auth_login_tickets")
    op.drop_index("ix_auth_login_tickets_portal", table_name="auth_login_tickets")
    op.drop_index("ix_auth_login_tickets_user_id", table_name="auth_login_tickets")
    op.drop_table("auth_login_tickets")

    op.drop_index("ix_auth_login_challenges_expires_at", table_name="auth_login_challenges")
    op.drop_index("ix_auth_login_challenges_challenge_hash", table_name="auth_login_challenges")
    op.drop_index("ix_auth_login_challenges_portal", table_name="auth_login_challenges")
    op.drop_index("ix_auth_login_challenges_user_id", table_name="auth_login_challenges")
    op.drop_table("auth_login_challenges")

    op.drop_index("ix_user_external_identities_provider", table_name="user_external_identities")
    op.drop_index("ix_user_external_identities_user_id", table_name="user_external_identities")
    op.drop_table("user_external_identities")

    op.drop_column("tenants", "onboarding_status")
