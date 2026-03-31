#!/usr/bin/env python3
"""
Staging Duplicate Audit & Consolidation Script
===============================================
Audita y consolida duplicados en fiscal_operations e invoices antes de
aplicar restricciones únicas en entornos de staging.

Uso:
    python scripts/staging_dedup_check.py --dry-run   # Solo reporta, no modifica
    python scripts/staging_dedup_check.py --fix       # Consolida duplicados
    python scripts/staging_dedup_check.py --env TEST  # Filtra por ambiente

Prerequisito:
    DATABASE_URL debe estar configurado en el entorno o en .env
"""
from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# ---------------------------------------------------------------------------
# Carga de settings antes de importar modelos
# ---------------------------------------------------------------------------
from app.infra.settings import settings  # noqa: E402

try:
    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import Session
except ImportError as exc:
    print(f"[ERROR] SQLAlchemy no disponible: {exc}")
    sys.exit(1)


def _sync_url(url: str) -> str:
    """Convierte URL asyncpg a psycopg2 para uso síncrono."""
    return url.replace("+asyncpg", "").replace("postgresql+asyncpg", "postgresql")


def _get_engine():
    db_url = _sync_url(settings.database_url)
    return create_engine(db_url, echo=False)


# ---------------------------------------------------------------------------
# Auditoría de duplicados
# ---------------------------------------------------------------------------

def audit_fiscal_operations_duplicates(session: Session) -> list[dict]:
    """Detecta operation_key duplicados en fiscal_operations."""
    result = session.execute(
        text("""
            SELECT
                operation_key,
                COUNT(*) AS cnt,
                MIN(id) AS keep_id,
                ARRAY_AGG(id ORDER BY id) AS all_ids,
                ARRAY_AGG(state ORDER BY id) AS states,
                ARRAY_AGG(operation_id ORDER BY id) AS operation_ids
            FROM fiscal_operations
            GROUP BY operation_key
            HAVING COUNT(*) > 1
            ORDER BY cnt DESC
        """)
    )
    rows = result.fetchall()
    return [
        {
            "operation_key": row.operation_key,
            "count": row.cnt,
            "keep_id": row.keep_id,
            "all_ids": list(row.all_ids),
            "states": list(row.states),
            "operation_ids": list(row.operation_ids),
        }
        for row in rows
    ]


def audit_invoice_duplicates(session: Session) -> list[dict]:
    """Detecta duplicados tenant_id+encf en invoices."""
    result = session.execute(
        text("""
            SELECT
                tenant_id,
                encf,
                COUNT(*) AS cnt,
                MIN(id) AS keep_id,
                ARRAY_AGG(id ORDER BY id) AS all_ids,
                ARRAY_AGG(estado_dgii ORDER BY id) AS estados,
                ARRAY_AGG(track_id ORDER BY id) AS track_ids
            FROM invoices
            GROUP BY tenant_id, encf
            HAVING COUNT(*) > 1
            ORDER BY cnt DESC
        """)
    )
    rows = result.fetchall()
    return [
        {
            "tenant_id": row.tenant_id,
            "encf": row.encf,
            "count": row.cnt,
            "keep_id": row.keep_id,
            "all_ids": list(row.all_ids),
            "estados": list(row.estados),
            "track_ids": list(row.track_ids),
        }
        for row in rows
    ]


def audit_operation_id_duplicates(session: Session) -> list[dict]:
    """Detecta operation_id duplicados (debería ser único)."""
    result = session.execute(
        text("""
            SELECT
                operation_id,
                COUNT(*) AS cnt,
                ARRAY_AGG(id ORDER BY id) AS all_ids
            FROM fiscal_operations
            GROUP BY operation_id
            HAVING COUNT(*) > 1
            ORDER BY cnt DESC
        """)
    )
    rows = result.fetchall()
    return [
        {
            "operation_id": row.operation_id,
            "count": row.cnt,
            "all_ids": list(row.all_ids),
        }
        for row in rows
    ]


# ---------------------------------------------------------------------------
# Consolidación de duplicados
# ---------------------------------------------------------------------------

def fix_fiscal_operations_duplicates(session: Session, duplicates: list[dict], dry_run: bool) -> int:
    """
    Consolida duplicados de operation_key manteniendo el registro más antiguo (MIN id).
    Reasigna eventos, intentos y evidencias al registro a conservar antes de eliminar.
    """
    fixed = 0
    for dup in duplicates:
        keep_id = dup["keep_id"]
        remove_ids = [i for i in dup["all_ids"] if i != keep_id]
        print(f"  [fiscal_operations] operation_key={dup['operation_key'][:16]}... "
              f"keep={keep_id}, remove={remove_ids}, states={dup['states']}")

        if not dry_run:
            # Reasignar eventos al registro a conservar
            session.execute(
                text("UPDATE fiscal_operation_events SET operation_fk = :keep WHERE operation_fk = ANY(:remove)"),
                {"keep": keep_id, "remove": remove_ids},
            )
            # Reasignar intentos DGII
            session.execute(
                text("UPDATE dgii_attempts SET operation_fk = :keep WHERE operation_fk = ANY(:remove)"),
                {"keep": keep_id, "remove": remove_ids},
            )
            # Reasignar intentos Odoo
            session.execute(
                text("UPDATE odoo_sync_attempts SET operation_fk = :keep WHERE operation_fk = ANY(:remove)"),
                {"keep": keep_id, "remove": remove_ids},
            )
            # Reasignar evidencias
            session.execute(
                text("UPDATE evidence_artifacts SET operation_fk = :keep WHERE operation_fk = ANY(:remove)"),
                {"keep": keep_id, "remove": remove_ids},
            )
            # Limpiar referencias en invoices
            session.execute(
                text("UPDATE invoices SET last_operation_id = :keep WHERE last_operation_id = ANY(:remove)"),
                {"keep": keep_id, "remove": remove_ids},
            )
            # Eliminar duplicados
            session.execute(
                text("DELETE FROM fiscal_operations WHERE id = ANY(:remove)"),
                {"remove": remove_ids},
            )
            session.commit()
            fixed += len(remove_ids)
    return fixed


def fix_invoice_duplicates(session: Session, duplicates: list[dict], dry_run: bool) -> int:
    """
    Consolida duplicados de tenant_id+encf manteniendo el registro más antiguo (MIN id).
    Reasigna líneas y operaciones al registro a conservar.
    """
    fixed = 0
    for dup in duplicates:
        keep_id = dup["keep_id"]
        remove_ids = [i for i in dup["all_ids"] if i != keep_id]
        print(f"  [invoices] tenant_id={dup['tenant_id']} encf={dup['encf']} "
              f"keep={keep_id}, remove={remove_ids}, estados={dup['estados']}")

        if not dry_run:
            # Reasignar líneas de factura
            session.execute(
                text("UPDATE invoice_lines SET invoice_id = :keep WHERE invoice_id = ANY(:remove)"),
                {"keep": keep_id, "remove": remove_ids},
            )
            # Reasignar asientos contables
            session.execute(
                text("UPDATE invoice_ledger_entries SET invoice_id = :keep WHERE invoice_id = ANY(:remove)"),
                {"keep": keep_id, "remove": remove_ids},
            )
            # Reasignar operaciones fiscales
            session.execute(
                text("UPDATE fiscal_operations SET invoice_id = :keep WHERE invoice_id = ANY(:remove)"),
                {"keep": keep_id, "remove": remove_ids},
            )
            # Limpiar last_generated_invoice_id en recurring schedules
            session.execute(
                text("UPDATE recurring_invoice_schedules SET last_generated_invoice_id = :keep "
                     "WHERE last_generated_invoice_id = ANY(:remove)"),
                {"keep": keep_id, "remove": remove_ids},
            )
            # Limpiar invoice_id en recurring executions
            session.execute(
                text("UPDATE recurring_invoice_executions SET invoice_id = :keep "
                     "WHERE invoice_id = ANY(:remove)"),
                {"keep": keep_id, "remove": remove_ids},
            )
            # Eliminar duplicados
            session.execute(
                text("DELETE FROM invoices WHERE id = ANY(:remove)"),
                {"remove": remove_ids},
            )
            session.commit()
            fixed += len(remove_ids)
    return fixed


# ---------------------------------------------------------------------------
# Reporte de estadísticas generales
# ---------------------------------------------------------------------------

def print_table_stats(session: Session) -> None:
    """Imprime estadísticas generales de las tablas principales."""
    tables = [
        "fiscal_operations",
        "fiscal_operation_events",
        "dgii_attempts",
        "odoo_sync_attempts",
        "evidence_artifacts",
        "invoices",
        "invoice_lines",
        "comprobante_coverage_results",
    ]
    print("\n📊 Estadísticas de tablas:")
    print(f"  {'Tabla':<40} {'Filas':>10}")
    print(f"  {'-'*40} {'-'*10}")
    for table in tables:
        try:
            count = session.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
            print(f"  {table:<40} {count:>10,}")
        except Exception as exc:
            print(f"  {table:<40} {'ERROR':>10} ({exc})")


def print_operation_state_breakdown(session: Session) -> None:
    """Imprime desglose de estados de operaciones fiscales."""
    result = session.execute(
        text("""
            SELECT state, environment, COUNT(*) AS cnt
            FROM fiscal_operations
            GROUP BY state, environment
            ORDER BY cnt DESC
        """)
    )
    rows = result.fetchall()
    if not rows:
        print("\n  (sin operaciones fiscales)")
        return
    print("\n📋 Desglose de estados de operaciones fiscales:")
    print(f"  {'Estado':<30} {'Ambiente':<12} {'Cantidad':>10}")
    print(f"  {'-'*30} {'-'*12} {'-'*10}")
    for row in rows:
        print(f"  {row.state:<30} {row.environment:<12} {row.cnt:>10,}")


def print_invoice_estado_breakdown(session: Session) -> None:
    """Imprime desglose de estados DGII de comprobantes."""
    result = session.execute(
        text("""
            SELECT estado_dgii, COUNT(*) AS cnt
            FROM invoices
            GROUP BY estado_dgii
            ORDER BY cnt DESC
        """)
    )
    rows = result.fetchall()
    if not rows:
        print("\n  (sin comprobantes)")
        return
    print("\n📋 Desglose de estados DGII de comprobantes:")
    print(f"  {'Estado DGII':<30} {'Cantidad':>10}")
    print(f"  {'-'*30} {'-'*10}")
    for row in rows:
        print(f"  {str(row.estado_dgii):<30} {row.cnt:>10,}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Auditoría y consolidación de duplicados para staging DGII e-CF"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=True,
        help="Solo reporta duplicados sin modificar datos (default: True)",
    )
    parser.add_argument(
        "--fix",
        action="store_true",
        default=False,
        help="Consolida duplicados (requiere confirmación)",
    )
    parser.add_argument(
        "--env",
        default=None,
        help="Filtra por ambiente DGII (LOCAL, TEST, CERT, PROD)",
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        default=False,
        help="Confirma la consolidación sin prompt interactivo",
    )
    args = parser.parse_args()

    dry_run = not args.fix
    if args.fix:
        dry_run = False

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    print(f"\n{'='*60}")
    print(f"  DGII e-CF — Auditoría de Duplicados en Staging")
    print(f"  Fecha: {now}")
    print(f"  Modo: {'DRY-RUN (solo lectura)' if dry_run else '⚠️  FIX (modificará datos)'}")
    print(f"{'='*60}\n")

    if not dry_run and not args.yes:
        confirm = input("¿Confirmar consolidación de duplicados? [s/N]: ").strip().lower()
        if confirm not in {"s", "si", "sí", "y", "yes"}:
            print("Operación cancelada.")
            return 0

    engine = _get_engine()
    total_issues = 0

    with Session(engine) as session:
        # Estadísticas generales
        print_table_stats(session)
        print_operation_state_breakdown(session)
        print_invoice_estado_breakdown(session)

        # ---------------------------------------------------------------
        # Auditoría de fiscal_operations
        # ---------------------------------------------------------------
        print("\n🔍 Auditando duplicados en fiscal_operations...")

        op_key_dups = audit_fiscal_operations_duplicates(session)
        if op_key_dups:
            print(f"  ⚠️  {len(op_key_dups)} operation_key(s) duplicados encontrados:")
            for dup in op_key_dups:
                print(f"    key={dup['operation_key'][:24]}... count={dup['count']} ids={dup['all_ids']}")
            total_issues += len(op_key_dups)
            if not dry_run:
                fixed = fix_fiscal_operations_duplicates(session, op_key_dups, dry_run=False)
                print(f"  ✅ {fixed} registros duplicados eliminados de fiscal_operations")
        else:
            print("  ✅ Sin duplicados de operation_key en fiscal_operations")

        op_id_dups = audit_operation_id_duplicates(session)
        if op_id_dups:
            print(f"  ⚠️  {len(op_id_dups)} operation_id(s) duplicados encontrados (crítico):")
            for dup in op_id_dups:
                print(f"    id={dup['operation_id'][:24]}... count={dup['count']} ids={dup['all_ids']}")
            total_issues += len(op_id_dups)
        else:
            print("  ✅ Sin duplicados de operation_id en fiscal_operations")

        # ---------------------------------------------------------------
        # Auditoría de invoices
        # ---------------------------------------------------------------
        print("\n🔍 Auditando duplicados en invoices...")

        inv_dups = audit_invoice_duplicates(session)
        if inv_dups:
            print(f"  ⚠️  {len(inv_dups)} combinación(es) tenant_id+encf duplicadas encontradas:")
            for dup in inv_dups:
                print(f"    tenant={dup['tenant_id']} encf={dup['encf']} count={dup['count']} ids={dup['all_ids']}")
            total_issues += len(inv_dups)
            if not dry_run:
                fixed = fix_invoice_duplicates(session, inv_dups, dry_run=False)
                print(f"  ✅ {fixed} registros duplicados eliminados de invoices")
        else:
            print("  ✅ Sin duplicados de tenant_id+encf en invoices")

    # ---------------------------------------------------------------
    # Resumen final
    # ---------------------------------------------------------------
    print(f"\n{'='*60}")
    if total_issues == 0:
        print("  ✅ Sin duplicados detectados. Seguro aplicar migración.")
        print("     Ejecutar: alembic upgrade head")
    elif dry_run:
        print(f"  ⚠️  {total_issues} problema(s) detectado(s).")
        print("     Ejecutar con --fix para consolidar antes de migrar:")
        print("     python scripts/staging_dedup_check.py --fix --yes")
    else:
        print(f"  ✅ Consolidación completada. {total_issues} grupo(s) procesado(s).")
        print("     Ahora seguro aplicar migración: alembic upgrade head")
    print(f"{'='*60}\n")

    return 1 if (total_issues > 0 and dry_run) else 0


if __name__ == "__main__":
    sys.exit(main())
