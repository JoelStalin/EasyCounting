#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.certificate_workflow.certificate_validation import validate_p12_file as validate


def main() -> int:
    parser = argparse.ArgumentParser(description="Valida certificado DGII (.p12/.pfx) y emite resultado JSON.")
    parser.add_argument("--file", required=True, help="Ruta al .p12/.pfx")
    parser.add_argument("--password", required=True, help="Password del PKCS#12")
    parser.add_argument("--expected-subject", default=None, help="Substring esperado en subject")
    parser.add_argument("--expected-serial", default=None, help="Serial esperado")
    parser.add_argument("--expected-rnc", default=None, help="RNC esperado en subject")
    args = parser.parse_args()

    result = validate(
        file_path=Path(args.file),
        password=args.password,
        expected_subject=args.expected_subject,
        expected_serial=args.expected_serial,
        expected_rnc=args.expected_rnc,
    )
    print(json.dumps(asdict(result), ensure_ascii=False))
    return 0 if result.valid else 1


if __name__ == "__main__":
    raise SystemExit(main())
