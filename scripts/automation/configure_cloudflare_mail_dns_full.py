from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import httpx


@dataclass
class CFConfig:
    api_token: str
    domain: str

    @classmethod
    def from_env(cls, domain: str) -> "CFConfig":
        token = os.getenv("CLOUDFLARE_API_TOKEN")
        if not token:
            raise ValueError(
                "Falta CLOUDFLARE_API_TOKEN. Configuralo en entorno antes de ejecutar."
            )
        return cls(api_token=token, domain=domain)


class CloudflareAPI:
    BASE = "https://api.cloudflare.com/client/v4"

    def __init__(self, cfg: CFConfig):
        self.cfg = cfg
        self.headers = {
            "Authorization": f"Bearer {cfg.api_token}",
            "Content-Type": "application/json",
        }

    def _request(self, method: str, path: str, **kwargs):
        url = f"{self.BASE}{path}"
        resp = httpx.request(method, url, headers=self.headers, timeout=30.0, **kwargs)
        resp.raise_for_status()
        body = resp.json()
        if not body.get("success", False):
            raise RuntimeError(f"Cloudflare API error: {body.get('errors')}")
        return body

    def get_zone_id(self) -> str:
        data = self._request("GET", f"/zones?name={self.cfg.domain}")
        result = data.get("result", [])
        if not result:
            raise RuntimeError(f"No existe zona para dominio {self.cfg.domain}")
        return result[0]["id"]

    def list_dns(self, zone_id: str, record_type: str | None = None, name: str | None = None) -> list[dict]:
        query = []
        if record_type:
            query.append(f"type={record_type}")
        if name:
            query.append(f"name={name}")
        suffix = "?" + "&".join(query) if query else ""
        data = self._request("GET", f"/zones/{zone_id}/dns_records{suffix}")
        return data.get("result", [])

    def create_dns(self, zone_id: str, payload: dict) -> dict:
        data = self._request("POST", f"/zones/{zone_id}/dns_records", json=payload)
        return data["result"]

    def update_dns(self, zone_id: str, record_id: str, payload: dict) -> dict:
        data = self._request("PUT", f"/zones/{zone_id}/dns_records/{record_id}", json=payload)
        return data["result"]

    def upsert_dns(self, zone_id: str, payload: dict) -> dict:
        rtype = payload["type"]
        name = payload["name"]
        matches = self.list_dns(zone_id, record_type=rtype, name=name)
        if matches:
            record_id = matches[0]["id"]
            return self.update_dns(zone_id, record_id, payload)
        return self.create_dns(zone_id, payload)


def build_payloads(args) -> list[dict]:
    payloads: list[dict] = []

    payloads.append(
        {
            "type": "A",
            "name": args.mail_host,
            "content": args.mail_ipv4,
            "ttl": 300,
            "proxied": False,
        }
    )

    if args.mail_ipv6:
        payloads.append(
            {
                "type": "AAAA",
                "name": args.mail_host,
                "content": args.mail_ipv6,
                "ttl": 300,
                "proxied": False,
            }
        )

    payloads.append(
        {
            "type": "MX",
            "name": args.domain,
            "content": args.mail_host,
            "priority": args.mx_priority,
            "ttl": 300,
        }
    )

    payloads.append(
        {
            "type": "TXT",
            "name": args.domain,
            "content": args.spf,
            "ttl": 300,
        }
    )

    payloads.append(
        {
            "type": "TXT",
            "name": f"_dmarc.{args.domain}",
            "content": args.dmarc,
            "ttl": 300,
        }
    )

    if args.dkim_selector and args.dkim_value:
        payloads.append(
            {
                "type": "TXT",
                "name": f"{args.dkim_selector}._domainkey.{args.domain}",
                "content": args.dkim_value,
                "ttl": 300,
            }
        )

    if args.enable_autodiscover:
        payloads.append(
            {
                "type": "CNAME",
                "name": f"autodiscover.{args.domain}",
                "content": args.mail_host,
                "ttl": 300,
                "proxied": False,
            }
        )

    return payloads


def main() -> int:
    parser = argparse.ArgumentParser(description="Configura DNS de correo completo en Cloudflare (real mode)")
    parser.add_argument("--domain", default="getupsoft.com.do")
    parser.add_argument("--mail-host", default="mail.getupsoft.com.do")
    parser.add_argument("--mail-ipv4", required=True)
    parser.add_argument("--mail-ipv6", default=None)
    parser.add_argument("--mx-priority", type=int, default=10)
    parser.add_argument("--spf", default="v=spf1 mx a:mail.getupsoft.com.do ~all")
    parser.add_argument("--dmarc", default="v=DMARC1; p=none; rua=mailto:postmaster@getupsoft.com.do; fo=1")
    parser.add_argument("--dkim-selector", default=None)
    parser.add_argument("--dkim-value", default=None)
    parser.add_argument("--enable-autodiscover", action="store_true")
    parser.add_argument("--output", default="docs/evidence/cloudflare_mail_dns_result.json")
    args = parser.parse_args()

    cfg = CFConfig.from_env(args.domain)
    api = CloudflareAPI(cfg)

    zone_id = api.get_zone_id()
    payloads = build_payloads(args)

    applied: list[dict] = []
    for payload in payloads:
        rec = api.upsert_dns(zone_id, payload)
        applied.append(
            {
                "id": rec.get("id"),
                "type": rec.get("type"),
                "name": rec.get("name"),
                "content": rec.get("content"),
                "priority": rec.get("priority"),
                "proxied": rec.get("proxied"),
                "ttl": rec.get("ttl"),
            }
        )

    result = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "domain": args.domain,
        "zone_id": zone_id,
        "mail_host": args.mail_host,
        "applied_records": applied,
    }

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")

    print(json.dumps(result, indent=2, ensure_ascii=False))
    print(f"\nEvidencia guardada en: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
