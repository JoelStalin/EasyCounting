#!/usr/bin/env python3
from __future__ import annotations

import json
import sys

from app.services.browser_mcp.dgii_postulacion import run_postulacion_emisor_flow


def main() -> int:
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
