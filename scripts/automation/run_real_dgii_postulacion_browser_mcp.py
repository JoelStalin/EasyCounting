#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys

from app.services.browser_mcp.dgii_context import load_context, resolve_active_errors
from app.services.browser_mcp.dgii_postulacion import run_postulacion_emisor_flow


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run real DGII postulacion flow via Browser MCP")
    parser.add_argument(
        "--session-mode",
        choices=["direct", "profile_clone"],
        default=None,
        help="Override DGII_SESSION_MODE for this run",
    )
    parser.add_argument(
        "--operator-id",
        default=None,
        help="Operator identifier for audit trail",
    )
    parser.add_argument(
        "--resolve-active-errors",
        action="store_true",
        help="Resolve active errors in DGII context before running the flow",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    if args.session_mode:
        os.environ["DGII_SESSION_MODE"] = args.session_mode
    if args.operator_id:
        os.environ["DGII_OPERATOR_ID"] = args.operator_id
    if args.resolve_active_errors:
        ctx = load_context()
        resolved = resolve_active_errors(
            ctx,
            cause="manual_pre_run_reset",
            solution=f"resolved from CLI by operator={args.operator_id or 'unknown'}",
        )
        print(json.dumps({"resolved_active_errors": resolved}, ensure_ascii=False))
    summary = run_postulacion_emisor_flow()
    print(json.dumps(summary, ensure_ascii=False))
    upload_job = summary.get("upload_job")
    if isinstance(upload_job, dict) and upload_job.get("status") == "completed":
        return 0
    if summary.get("upload_attempted") is False:
        return 3
    if isinstance(upload_job, dict):
        return 1
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # noqa: BLE001
        print(str(exc), file=sys.stderr)
        raise SystemExit(1)
