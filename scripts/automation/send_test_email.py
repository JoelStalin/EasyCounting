from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.services.email_service import EmailAttachment, EmailPayload, get_email_service


def main() -> int:
    parser = argparse.ArgumentParser(description="Send a test email using the project SMTP configuration.")
    parser.add_argument("--to", required=True)
    parser.add_argument("--subject", default="Prueba SMTP GetUpSoft")
    parser.add_argument("--text", default="Correo de prueba enviado desde el servicio SMTP del proyecto.")
    parser.add_argument("--html", default=None)
    parser.add_argument("--attach", action="append", default=[])
    args = parser.parse_args()

    attachments = [EmailAttachment.from_path(path) for path in args.attach]
    payload = EmailPayload(
        to=args.to,
        subject=args.subject,
        text_body=args.text,
        html_body=args.html,
        attachments=attachments,
    )
    get_email_service().send(payload)
    print(f"Correo enviado a {args.to}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
