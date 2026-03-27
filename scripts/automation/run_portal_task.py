#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from app.dgii_portal_automation.portal_runner import run_portal_task


def main() -> int:
    parser = argparse.ArgumentParser(description="Run unified DGII portal task (selenium/playwright).")
    parser.add_argument("--task", required=True, help="task_name")
    parser.add_argument("--case-id", required=True)
    parser.add_argument("--execution-id", required=True)
    parser.add_argument("--engine", default="selenium", choices=["selenium", "playwright"])
    parser.add_argument("--payload-json", default="{}", help="JSON string payload")
    parser.add_argument("--payload-file", default="", help="Path to JSON payload file")
    args = parser.parse_args()

    payload: dict = {}
    if args.payload_file:
        payload = json.loads(Path(args.payload_file).read_text(encoding="utf-8"))
    elif args.payload_json:
        payload = json.loads(args.payload_json)

    result = run_portal_task(
        task_name=args.task,
        case_id=args.case_id,
        execution_id=args.execution_id,
        input_payload=payload,
        engine=args.engine,
    )
    print(json.dumps(result.__dict__, ensure_ascii=False, indent=2))
    return 0 if result.status in {"OK", "DONE"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
