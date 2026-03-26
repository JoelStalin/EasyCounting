"""Durable fiscal operations and accounting hardening.

Revision ID: 20260325_0001
Revises: 20260319_0004
Create Date: 2026-03-25
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision = "20260325_0001"
down_revision = "20260319_0004"
branch_labels = None
depends_on = None


def _inspector():
    return inspect(op.get_bind())


def _has_table(table_name: str) -> bool:
    return table_name in _inspector().get_table_names()


def _has_column(table_name: str, column_name: str) -> bool:
    if not _has_table(table_name):
        return False
    return any(column["name"] == column_name for column in _inspector().get_columns(table_name))


def _has_index(table_name: str, index_name: str) -> bool:
    if not _has_table(table_name):
        return False
    return any(index["name"] == index_name for index in _inspector().get_indexes(table_name))


def _has_unique_constraint(table_name: str, constraint_name: str) -> bool:
    if not _has_table(table_name):
        return False
    return any(constraint["name"] == constraint_name for constraint in _inspector().get_unique_constraints(table_name))


def _has_foreign_key(table_name: str, constraint_name: str) -> bool:
    if not _has_table(table_name):
        return False
    return any(fk["name"] == constraint_name for fk in _inspector().get_foreign_keys(table_name))


def _add_column_if_missing(table_name: str, column: sa.Column) -> None:
    if not _has_column(table_name, column.name):
        with op.batch_alter_table(table_name) as batch_op:
            batch_op.add_column(column)


def _create_index_if_missing(index_name: str, table_name: str, columns: list[str], *, unique: bool = False) -> None:
    if not _has_index(table_name, index_name):
        op.create_index(index_name, table_name, columns, unique=unique)


def _drop_index_if_exists(index_name: str, table_name: str) -> None:
    if _has_index(table_name, index_name):
        op.drop_index(index_name, table_name=table_name)


def upgrade() -> None:
    if not _has_table("user_profiles"):
        op.create_table(
            "user_profiles",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
            sa.Column("first_name", sa.String(length=120), nullable=True),
            sa.Column("last_name", sa.String(length=120), nullable=True),
            sa.Column("avatar_path", sa.String(length=255), nullable=True),
            sa.Column("alternate_email", sa.String(length=255), nullable=True),
            sa.Column("phone_primary", sa.String(length=30), nullable=True),
            sa.Column("phone_secondary", sa.String(length=30), nullable=True),
            sa.Column("address_line_1", sa.String(length=255), nullable=True),
            sa.Column("address_line_2", sa.String(length=255), nullable=True),
            sa.Column("country", sa.String(length=80), nullable=True),
            sa.Column("province", sa.String(length=120), nullable=True),
            sa.Column("municipality", sa.String(length=120), nullable=True),
            sa.Column("sector", sa.String(length=120), nullable=True),
            sa.Column("postal_code", sa.String(length=20), nullable=True),
            sa.Column("economic_activity", sa.String(length=255), nullable=True),
            sa.Column("locale", sa.String(length=20), nullable=False, server_default="es-DO"),
            sa.Column("timezone", sa.String(length=64), nullable=False, server_default="America/Santo_Domingo"),
            sa.Column("notification_settings_json", sa.Text(), nullable=True),
            sa.Column("security_settings_json", sa.Text(), nullable=True),
            sa.Column("regional_settings_json", sa.Text(), nullable=True),
            sa.Column("privacy_settings_json", sa.Text(), nullable=True),
            sa.UniqueConstraint("user_id", name="uq_user_profiles_user"),
        )

    if not _has_table("fiscal_profiles"):
        op.create_table(
            "fiscal_profiles",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.Column("owner_type", sa.String(length=20), nullable=False, server_default="TENANT"),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=True),
            sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=True),
            sa.Column("persona_tipo", sa.String(length=20), nullable=True),
            sa.Column("tax_id_type", sa.String(length=20), nullable=True),
            sa.Column("tax_id", sa.String(length=20), nullable=True),
            sa.Column("legal_name", sa.String(length=255), nullable=True),
            sa.Column("trade_name", sa.String(length=255), nullable=True),
            sa.Column("fiscal_address", sa.String(length=255), nullable=True),
            sa.Column("country", sa.String(length=80), nullable=True),
            sa.Column("province", sa.String(length=120), nullable=True),
            sa.Column("municipality", sa.String(length=120), nullable=True),
            sa.Column("sector", sa.String(length=120), nullable=True),
            sa.Column("postal_code", sa.String(length=20), nullable=True),
            sa.Column("phone", sa.String(length=30), nullable=True),
            sa.Column("email", sa.String(length=255), nullable=True),
            sa.Column("representative_name", sa.String(length=255), nullable=True),
            sa.Column("commercial_activity", sa.String(length=255), nullable=True),
            sa.Column("dgii_certificate_ref", sa.String(length=255), nullable=True),
            sa.Column("dgii_certificate_subject", sa.String(length=255), nullable=True),
            sa.Column("billing_email", sa.String(length=255), nullable=True),
            sa.Column("is_billing_ready_override", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.UniqueConstraint("user_id", name="uq_fiscal_profiles_user"),
            sa.UniqueConstraint("tenant_id", name="uq_fiscal_profiles_tenant"),
        )
    _create_index_if_missing("ix_fiscal_profiles_tax_id", "fiscal_profiles", ["tax_id"])

    if _has_table("tenant_settings"):
        _add_column_if_missing("tenant_settings", sa.Column("rounding_policy", sa.String(length=32), nullable=False, server_default="HALF_UP"))
        _add_column_if_missing("tenant_settings", sa.Column("odoo_sync_enabled", sa.Boolean(), nullable=False, server_default=sa.false()))
        _add_column_if_missing("tenant_settings", sa.Column("odoo_api_url", sa.String(length=255), nullable=True))
        _add_column_if_missing("tenant_settings", sa.Column("odoo_database", sa.String(length=120), nullable=True))
        _add_column_if_missing("tenant_settings", sa.Column("odoo_company_id", sa.Integer(), nullable=True))
        _add_column_if_missing("tenant_settings", sa.Column("odoo_sales_journal_id", sa.Integer(), nullable=True))
        _add_column_if_missing("tenant_settings", sa.Column("odoo_purchase_journal_id", sa.Integer(), nullable=True))
        _add_column_if_missing("tenant_settings", sa.Column("odoo_fiscal_position_id", sa.Integer(), nullable=True))
        _add_column_if_missing("tenant_settings", sa.Column("odoo_payment_term_id", sa.Integer(), nullable=True))
        _add_column_if_missing("tenant_settings", sa.Column("odoo_currency_id", sa.Integer(), nullable=True))
        _add_column_if_missing("tenant_settings", sa.Column("odoo_customer_document_type_id", sa.Integer(), nullable=True))
        _add_column_if_missing("tenant_settings", sa.Column("odoo_vendor_document_type_id", sa.Integer(), nullable=True))
        _add_column_if_missing("tenant_settings", sa.Column("odoo_credit_note_document_type_id", sa.Integer(), nullable=True))
        _add_column_if_missing("tenant_settings", sa.Column("odoo_debit_note_document_type_id", sa.Integer(), nullable=True))
        _add_column_if_missing("tenant_settings", sa.Column("odoo_sales_tax_id", sa.Integer(), nullable=True))
        _add_column_if_missing("tenant_settings", sa.Column("odoo_purchase_tax_id", sa.Integer(), nullable=True))
        _add_column_if_missing("tenant_settings", sa.Column("odoo_zero_tax_id", sa.Integer(), nullable=True))
        _add_column_if_missing("tenant_settings", sa.Column("odoo_partner_vat_prefix", sa.String(length=12), nullable=True))
        _add_column_if_missing("tenant_settings", sa.Column("odoo_journal_code_hint", sa.String(length=32), nullable=True))
        _add_column_if_missing("tenant_settings", sa.Column("odoo_api_key_ref", sa.String(length=128), nullable=True))

    if _has_table("invoice_ledger_entries"):
        with op.batch_alter_table("invoice_ledger_entries") as batch_op:
            batch_op.alter_column("debit", existing_type=sa.Numeric(16, 2), type_=sa.Numeric(20, 6), existing_nullable=False)
            batch_op.alter_column("credit", existing_type=sa.Numeric(16, 2), type_=sa.Numeric(20, 6), existing_nullable=False)

    if _has_table("invoices"):
        _add_column_if_missing("invoices", sa.Column("expiration_at", sa.DateTime(), nullable=True))
        _add_column_if_missing("invoices", sa.Column("issuer_tenant_id", sa.Integer(), sa.ForeignKey("tenants.id", ondelete="SET NULL"), nullable=True))
        _add_column_if_missing("invoices", sa.Column("issuer_fiscal_profile_id", sa.Integer(), sa.ForeignKey("fiscal_profiles.id", ondelete="SET NULL"), nullable=True))
        _add_column_if_missing("invoices", sa.Column("receiver_fiscal_profile_id", sa.Integer(), sa.ForeignKey("fiscal_profiles.id", ondelete="SET NULL"), nullable=True))
        _add_column_if_missing("invoices", sa.Column("issuer_tax_id", sa.String(length=20), nullable=True))
        _add_column_if_missing("invoices", sa.Column("issuer_legal_name", sa.String(length=255), nullable=True))
        _add_column_if_missing("invoices", sa.Column("issuer_trade_name", sa.String(length=255), nullable=True))
        _add_column_if_missing("invoices", sa.Column("issuer_address", sa.String(length=255), nullable=True))
        _add_column_if_missing("invoices", sa.Column("issuer_municipality", sa.String(length=120), nullable=True))
        _add_column_if_missing("invoices", sa.Column("issuer_province", sa.String(length=120), nullable=True))
        _add_column_if_missing("invoices", sa.Column("rnc_receptor", sa.String(length=11), nullable=True))
        _add_column_if_missing("invoices", sa.Column("receptor_nombre", sa.String(length=255), nullable=True))
        _add_column_if_missing("invoices", sa.Column("receptor_direccion", sa.String(length=255), nullable=True))
        _add_column_if_missing("invoices", sa.Column("receptor_municipio", sa.String(length=120), nullable=True))
        _add_column_if_missing("invoices", sa.Column("receptor_provincia", sa.String(length=120), nullable=True))
        _add_column_if_missing("invoices", sa.Column("ri_html_path", sa.String(length=255), nullable=True))
        _add_column_if_missing("invoices", sa.Column("ri_pdf_path", sa.String(length=255), nullable=True))
        _add_column_if_missing("invoices", sa.Column("ri_generated_at", sa.DateTime(), nullable=True))
        _add_column_if_missing("invoices", sa.Column("qr_url", sa.String(length=512), nullable=True))
        _add_column_if_missing("invoices", sa.Column("currency", sa.String(length=3), nullable=False, server_default="DOP"))
        _add_column_if_missing("invoices", sa.Column("subtotal_source", sa.Numeric(20, 6), nullable=False, server_default="0"))
        _add_column_if_missing("invoices", sa.Column("discount_total_source", sa.Numeric(20, 6), nullable=False, server_default="0"))
        _add_column_if_missing("invoices", sa.Column("tax_total_source", sa.Numeric(20, 6), nullable=False, server_default="0"))
        _add_column_if_missing("invoices", sa.Column("total_fiscal", sa.Numeric(20, 6), nullable=False, server_default="0"))
        _add_column_if_missing("invoices", sa.Column("total_accounting", sa.Numeric(20, 6), nullable=False, server_default="0"))
        _add_column_if_missing("invoices", sa.Column("rounding_delta", sa.Numeric(20, 6), nullable=False, server_default="0"))
        _add_column_if_missing("invoices", sa.Column("odoo_move_id", sa.String(length=64), nullable=True))
        _add_column_if_missing("invoices", sa.Column("odoo_move_name", sa.String(length=128), nullable=True))
        _add_column_if_missing("invoices", sa.Column("odoo_sync_state", sa.String(length=32), nullable=False, server_default="PENDING"))
        _add_column_if_missing("invoices", sa.Column("odoo_synced_at", sa.DateTime(), nullable=True))
        _add_column_if_missing("invoices", sa.Column("last_operation_id", sa.Integer(), nullable=True))
        with op.batch_alter_table("invoices") as batch_op:
            batch_op.alter_column("total", existing_type=sa.Numeric(16, 2), type_=sa.Numeric(20, 6), existing_nullable=True)

    _create_index_if_missing("ix_invoices_estado", "invoices", ["estado_dgii"])
    _create_index_if_missing("ix_invoices_rnc_receptor", "invoices", ["rnc_receptor"])
    if _has_table("invoices") and not _has_unique_constraint("invoices", "ux_invoices_tenant_encf"):
        with op.batch_alter_table("invoices") as batch_op:
            batch_op.create_unique_constraint("ux_invoices_tenant_encf", ["tenant_id", "encf"])

    if not _has_table("invoice_lines"):
        op.create_table(
            "invoice_lines",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
            sa.Column("invoice_id", sa.Integer(), sa.ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False),
            sa.Column("line_number", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("cantidad", sa.Numeric(20, 6), nullable=False, server_default="1"),
            sa.Column("billing_indicator", sa.String(length=20), nullable=True),
            sa.Column("descripcion", sa.String(length=255), nullable=False),
            sa.Column("unidad_medida", sa.String(length=40), nullable=True),
            sa.Column("precio_unitario", sa.Numeric(20, 6), nullable=False, server_default="0"),
            sa.Column("discount_amount", sa.Numeric(20, 6), nullable=False, server_default="0"),
            sa.Column("line_subtotal", sa.Numeric(20, 6), nullable=False, server_default="0"),
            sa.Column("itbis_rate", sa.Numeric(8, 4), nullable=True),
            sa.Column("itbis_amount", sa.Numeric(20, 6), nullable=False, server_default="0"),
            sa.Column("other_tax_amount", sa.Numeric(20, 6), nullable=False, server_default="0"),
            sa.Column("line_total", sa.Numeric(20, 6), nullable=False, server_default="0"),
        )
    _create_index_if_missing("ix_invoice_lines_invoice_id", "invoice_lines", ["invoice_id"])

    if not _has_table("fiscal_operations"):
        op.create_table(
            "fiscal_operations",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
            sa.Column("invoice_id", sa.Integer(), sa.ForeignKey("invoices.id", ondelete="SET NULL"), nullable=True),
            sa.Column("operation_id", sa.String(length=64), nullable=False),
            sa.Column("operation_key", sa.String(length=64), nullable=False),
            sa.Column("correlation_id", sa.String(length=64), nullable=False),
            sa.Column("request_id", sa.String(length=128), nullable=True),
            sa.Column("environment", sa.String(length=16), nullable=False, server_default="TEST"),
            sa.Column("source_system", sa.String(length=32), nullable=False, server_default="EASYCOUNTING"),
            sa.Column("document_type", sa.String(length=12), nullable=False),
            sa.Column("document_number", sa.String(length=64), nullable=True),
            sa.Column("state", sa.String(length=40), nullable=False, server_default="QUEUED"),
            sa.Column("payload_hash", sa.String(length=64), nullable=True),
            sa.Column("currency", sa.String(length=3), nullable=False, server_default="DOP"),
            sa.Column("amount_total", sa.Numeric(20, 6), nullable=False, server_default="0"),
            sa.Column("dgii_track_id", sa.String(length=64), nullable=True),
            sa.Column("dgii_status", sa.String(length=40), nullable=True),
            sa.Column("odoo_sync_state", sa.String(length=32), nullable=False, server_default="PENDING"),
            sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("initiated_by", sa.String(length=255), nullable=True),
            sa.Column("browser_mode", sa.String(length=32), nullable=True),
            sa.Column("last_error_code", sa.String(length=64), nullable=True),
            sa.Column("last_error_message", sa.Text(), nullable=True),
            sa.Column("started_at", sa.DateTime(), nullable=False),
            sa.Column("completed_at", sa.DateTime(), nullable=True),
            sa.Column("last_transition_at", sa.DateTime(), nullable=False),
            sa.Column("metadata_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
            sa.UniqueConstraint("operation_id", name="uq_fiscal_operations_operation_id"),
            sa.UniqueConstraint("operation_key", name="uq_fiscal_operations_operation_key"),
        )
    _create_index_if_missing("ix_fiscal_operations_tenant_state", "fiscal_operations", ["tenant_id", "state"])
    _create_index_if_missing("ix_fiscal_operations_track_id", "fiscal_operations", ["dgii_track_id"])
    _create_index_if_missing("ix_fiscal_operations_document", "fiscal_operations", ["document_type", "document_number"])

    if not _has_table("fiscal_operation_events"):
        op.create_table(
            "fiscal_operation_events",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.Column("operation_fk", sa.Integer(), sa.ForeignKey("fiscal_operations.id", ondelete="CASCADE"), nullable=False),
            sa.Column("status", sa.String(length=40), nullable=False),
            sa.Column("title", sa.String(length=120), nullable=False),
            sa.Column("message", sa.Text(), nullable=True),
            sa.Column("stage", sa.String(length=64), nullable=True),
            sa.Column("duration_ms", sa.Integer(), nullable=True),
            sa.Column("details_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
            sa.Column("occurred_at", sa.DateTime(), nullable=False),
        )
    _create_index_if_missing("ix_fiscal_operation_events_operation_id", "fiscal_operation_events", ["operation_fk", "id"])
    _create_index_if_missing("ix_fiscal_operation_events_status", "fiscal_operation_events", ["status"])
    _create_index_if_missing("ix_fiscal_operation_events_occurred_at", "fiscal_operation_events", ["occurred_at"])

    if not _has_table("dgii_attempts"):
        op.create_table(
            "dgii_attempts",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.Column("operation_fk", sa.Integer(), sa.ForeignKey("fiscal_operations.id", ondelete="CASCADE"), nullable=False),
            sa.Column("attempt_no", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("endpoint", sa.String(length=255), nullable=False),
            sa.Column("status", sa.String(length=32), nullable=False, server_default="PENDING"),
            sa.Column("http_status", sa.Integer(), nullable=True),
            sa.Column("request_payload_hash", sa.String(length=64), nullable=True),
            sa.Column("request_headers_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
            sa.Column("immediate_response_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
            sa.Column("track_id", sa.String(length=64), nullable=True),
            sa.Column("error_message", sa.Text(), nullable=True),
            sa.Column("started_at", sa.DateTime(), nullable=False),
            sa.Column("finished_at", sa.DateTime(), nullable=True),
            sa.Column("latency_ms", sa.Integer(), nullable=True),
        )
    _create_index_if_missing("ix_dgii_attempts_operation", "dgii_attempts", ["operation_fk", "attempt_no"])
    _create_index_if_missing("ix_dgii_attempts_track_id", "dgii_attempts", ["track_id"])

    if not _has_table("odoo_sync_attempts"):
        op.create_table(
            "odoo_sync_attempts",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.Column("operation_fk", sa.Integer(), sa.ForeignKey("fiscal_operations.id", ondelete="CASCADE"), nullable=False),
            sa.Column("attempt_no", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("status", sa.String(length=32), nullable=False, server_default="PENDING"),
            sa.Column("remote_model", sa.String(length=64), nullable=False, server_default="account.move"),
            sa.Column("remote_record_id", sa.String(length=64), nullable=True),
            sa.Column("remote_name", sa.String(length=128), nullable=True),
            sa.Column("payload_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
            sa.Column("response_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
            sa.Column("error_message", sa.Text(), nullable=True),
            sa.Column("started_at", sa.DateTime(), nullable=False),
            sa.Column("finished_at", sa.DateTime(), nullable=True),
            sa.Column("latency_ms", sa.Integer(), nullable=True),
        )
    _create_index_if_missing("ix_odoo_sync_attempts_operation", "odoo_sync_attempts", ["operation_fk", "attempt_no"])
    _create_index_if_missing("ix_odoo_sync_attempts_remote", "odoo_sync_attempts", ["remote_model", "remote_record_id"])

    if not _has_table("evidence_artifacts"):
        op.create_table(
            "evidence_artifacts",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.Column("operation_fk", sa.Integer(), sa.ForeignKey("fiscal_operations.id", ondelete="CASCADE"), nullable=False),
            sa.Column("artifact_type", sa.String(length=40), nullable=False),
            sa.Column("file_path", sa.String(length=512), nullable=False),
            sa.Column("content_type", sa.String(length=128), nullable=True),
            sa.Column("checksum", sa.String(length=64), nullable=True),
            sa.Column("size_bytes", sa.Integer(), nullable=True),
            sa.Column("metadata_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        )
    _create_index_if_missing("ix_evidence_artifacts_operation", "evidence_artifacts", ["operation_fk", "artifact_type"])

    if not _has_table("comprobante_coverage_results"):
        op.create_table(
            "comprobante_coverage_results",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.Column("environment", sa.String(length=16), nullable=False, server_default="TEST"),
            sa.Column("document_type", sa.String(length=12), nullable=False),
            sa.Column("classification", sa.String(length=64), nullable=True),
            sa.Column("odoo_supported", sa.String(length=32), nullable=False, server_default="UNKNOWN"),
            sa.Column("easycounting_supported", sa.String(length=32), nullable=False, server_default="UNKNOWN"),
            sa.Column("dgii_supported", sa.String(length=32), nullable=False, server_default="UNKNOWN"),
            sa.Column("sandbox_supported", sa.String(length=32), nullable=False, server_default="UNKNOWN"),
            sa.Column("supports_amount_0001", sa.String(length=32), nullable=False, server_default="UNKNOWN"),
            sa.Column("minimum_supported_amount", sa.Numeric(20, 6), nullable=True),
            sa.Column("last_operation_id", sa.String(length=64), nullable=True),
            sa.Column("result_status", sa.String(length=32), nullable=False, server_default="PENDING"),
            sa.Column("restriction_source", sa.String(length=64), nullable=True),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("evidence_path", sa.String(length=512), nullable=True),
            sa.UniqueConstraint("environment", "document_type", name="uq_comprobante_coverage_environment_type"),
        )
    _create_index_if_missing("ix_comprobante_coverage_results_document_type", "comprobante_coverage_results", ["document_type"])

    if _has_table("invoices") and _has_column("invoices", "last_operation_id") and not _has_foreign_key("invoices", "fk_invoices_last_operation_id_fiscal_operations"):
        with op.batch_alter_table("invoices") as batch_op:
            batch_op.create_foreign_key(
                "fk_invoices_last_operation_id_fiscal_operations",
                "fiscal_operations",
                ["last_operation_id"],
                ["id"],
                ondelete="SET NULL",
            )


def downgrade() -> None:
    if _has_table("invoices") and _has_foreign_key("invoices", "fk_invoices_last_operation_id_fiscal_operations"):
        with op.batch_alter_table("invoices") as batch_op:
            batch_op.drop_constraint("fk_invoices_last_operation_id_fiscal_operations", type_="foreignkey")

    for index_name, table_name in [
        ("ix_comprobante_coverage_results_document_type", "comprobante_coverage_results"),
        ("ix_evidence_artifacts_operation", "evidence_artifacts"),
        ("ix_odoo_sync_attempts_remote", "odoo_sync_attempts"),
        ("ix_odoo_sync_attempts_operation", "odoo_sync_attempts"),
        ("ix_dgii_attempts_track_id", "dgii_attempts"),
        ("ix_dgii_attempts_operation", "dgii_attempts"),
        ("ix_fiscal_operation_events_occurred_at", "fiscal_operation_events"),
        ("ix_fiscal_operation_events_status", "fiscal_operation_events"),
        ("ix_fiscal_operation_events_operation_id", "fiscal_operation_events"),
        ("ix_fiscal_operations_document", "fiscal_operations"),
        ("ix_fiscal_operations_track_id", "fiscal_operations"),
        ("ix_fiscal_operations_tenant_state", "fiscal_operations"),
        ("ix_invoice_lines_invoice_id", "invoice_lines"),
        ("ix_invoices_rnc_receptor", "invoices"),
        ("ix_invoices_estado", "invoices"),
        ("ix_fiscal_profiles_tax_id", "fiscal_profiles"),
    ]:
        _drop_index_if_exists(index_name, table_name)

    for table_name in [
        "comprobante_coverage_results",
        "evidence_artifacts",
        "odoo_sync_attempts",
        "dgii_attempts",
        "fiscal_operation_events",
        "fiscal_operations",
        "invoice_lines",
        "fiscal_profiles",
        "user_profiles",
    ]:
        if _has_table(table_name):
            op.drop_table(table_name)
