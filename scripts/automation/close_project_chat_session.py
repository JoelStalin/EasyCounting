from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.chat_memory.cli import main as save_chat_history_main
from app.chat_memory.compliance import assess_chat_memory_compliance


def main(argv: list[str] | None = None) -> int:
    args = list(argv or sys.argv[1:])
    if "--close-session" not in args:
        args.append("--close-session")
    exit_code = save_chat_history_main(args)
    if exit_code != 0:
        return exit_code
    report = assess_chat_memory_compliance(ROOT)
    print(json.dumps({"compliance": report}, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "compliant" else 1


if __name__ == "__main__":
    raise SystemExit(main())
