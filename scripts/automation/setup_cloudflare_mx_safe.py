#!/usr/bin/env python3
"""
Script seguro para configurar registros MX en Cloudflare usando API Token.

USO:
    python scripts/automation/setup_cloudflare_mx_safe.py \
      --domain getupsoft.com.do \
      --mx-host mail.getupsoft.com.do \
      --mx-priority 10

REQUERIMIENTOS:
    - Variable de entorno: CLOUDFLARE_API_TOKEN
    - httpx instalado: pip install httpx
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path

try:
    import httpx
except ImportError:
    print("ERROR: 'httpx' no instalado. Ejecuta:")
    print("  pip install httpx")
    sys.exit(1)


@dataclass
class CloudflareConfig:
    api_token: str
    domain: str
    zone_id: str | None = None

    @classmethod
    def from_env(cls, domain: str) -> CloudflareConfig:
        """Crear config desde variables de entorno."""
        api_token = os.getenv("CLOUDFLARE_API_TOKEN")
        if not api_token:
            raise ValueError(
                "Variable de entorno CLOUDFLARE_API_TOKEN no configurada.\n"
                "Obtén el token en: https://dash.cloudflare.com/profile/api-tokens\n"
                "Luego ejecuta:\n"
                "  $env:CLOUDFLARE_API_TOKEN = 'tu-token-aqui'"
            )
        return cls(api_token=api_token, domain=domain)


class CloudflareClient:
    """Cliente HTTP para API de Cloudflare."""

    BASE_URL = "https://api.cloudflare.com/client/v4"

    def __init__(self, config: CloudflareConfig):
        self.config = config
        self.headers = {
            "Authorization": f"Bearer {config.api_token}",
            "Content-Type": "application/json",
        }

    def get_zone_id(self, domain: str) -> str:
        """Obtener Zone ID para un dominio."""
        url = f"{self.BASE_URL}/zones?name={domain}"
        response = httpx.get(url, headers=self.headers)
        response.raise_for_status()

        data = response.json()
        if not data.get("result"):
            raise ValueError(f"Zona no encontrada para dominio: {domain}")

        return data["result"][0]["id"]

    def get_dns_records(self, zone_id: str, record_type: str = None) -> list[dict]:
        """Obtener registros DNS de una zona."""
        url = f"{self.BASE_URL}/zones/{zone_id}/dns_records"
        params = {}
        if record_type:
            params["type"] = record_type

        response = httpx.get(url, headers=self.headers, params=params)
        response.raise_for_status()

        return response.json().get("result", [])

    def create_mx_record(
        self, zone_id: str, name: str, mail_server: str, priority: int
    ) -> dict:
        """Crear registro MX."""
        url = f"{self.BASE_URL}/zones/{zone_id}/dns_records"
        data = {
            "type": "MX",
            "name": name,
            "content": mail_server,
            "priority": priority,
            "ttl": 3600,
        }

        response = httpx.post(url, headers=self.headers, json=data)
        response.raise_for_status()

        return response.json().get("result", {})

    def create_txt_record(self, zone_id: str, name: str, content: str) -> dict:
        """Crear registro TXT (SPF, DKIM, etc)."""
        url = f"{self.BASE_URL}/zones/{zone_id}/dns_records"
        data = {
            "type": "TXT",
            "name": name,
            "content": content,
            "ttl": 3600,
        }

        response = httpx.post(url, headers=self.headers, json=data)
        response.raise_for_status()

        return response.json().get("result", {})


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Configurar registros MX en Cloudflare (seguro, sin hardcoded secrets)"
    )
    parser.add_argument("--domain", required=True, help="Dominio (ej: getupsoft.com.do)")
    parser.add_argument(
        "--mx-host", required=True, help="Servidor de mail (ej: mail.getupsoft.com.do)"
    )
    parser.add_argument("--mx-priority", type=int, default=10, help="Prioridad MX (default: 10)")
    parser.add_argument("--spf-record", help="Registro SPF (default: v=spf1 ~all)")
    parser.add_argument("--output", type=Path, help="Guardar resultado en archivo JSON")
    args = parser.parse_args()

    try:
        # Crear configuración
        config = CloudflareConfig.from_env(domain=args.domain)
        client = CloudflareClient(config)

        print(f"📡 Configurando registros MX para: {args.domain}")
        print()

        # Obtener Zone ID
        print("1️⃣ Obteniendo Zone ID...")
        zone_id = client.get_zone_id(args.domain)
        print(f"   ✓ Zone ID: {zone_id}")
        print()

        # Revisar registros MX actuales
        print("2️⃣ Revisando registros MX actuales...")
        mx_records = client.get_dns_records(zone_id, "MX")
        if mx_records:
            for record in mx_records:
                print(f"   • {record['name']} MX {record['priority']} → {record['content']}")
        else:
            print("   • No hay registros MX actualmente")
        print()

        # Crear nuevo registro MX
        print("3️⃣ Creando nuevo registro MX...")
        mx_record = client.create_mx_record(
            zone_id=zone_id,
            name="@",
            mail_server=args.mx_host,
            priority=args.mx_priority,
        )
        print(f"   ✓ MX Creado: {mx_record['name']} MX {mx_record['priority']} → {mx_record['content']}")
        print(f"   Record ID: {mx_record['id']}")
        print()

        # Crear registro SPF (opcional)
        if args.spf_record:
            print("4️⃣ Creando registro SPF...")
            spf_record = client.create_txt_record(zone_id=zone_id, name="@", content=args.spf_record)
            print(f"   ✓ SPF Creado: {spf_record['content']}")
            print()
        else:
            print("4️⃣ SPF no especificado, usando predeterminado...")
            spf_content = "v=spf1 ~all"
            spf_record = client.create_txt_record(zone_id=zone_id, name="@", content=spf_content)
            print(f"   ✓ SPF Creado: {spf_record['content']}")
            print()

        # Guardar resultado
        result = {
            "timestamp": __import__("datetime").datetime.utcnow().isoformat(),
            "domain": args.domain,
            "zone_id": zone_id,
            "mx_record": {
                "id": mx_record["id"],
                "name": mx_record["name"],
                "type": mx_record["type"],
                "content": mx_record["content"],
                "priority": mx_record["priority"],
            },
            "spf_record": {
                "id": spf_record["id"],
                "type": spf_record["type"],
                "content": spf_record["content"],
            },
        }

        if args.output:
            args.output.write_text(json.dumps(result, indent=2))
            print(f"📁 Resultado guardado en: {args.output}")

        print("\n✅ Configuración de MX completada exitosamente")
        print("\n⏳ Esperando propagación DNS (5-10 minutos)...")
        print("   Luego verifica con:")
        print(f"   nslookup -type=MX {args.domain} 8.8.8.8")

        return 0

    except KeyError as e:
        print(f"❌ Error: {e}")
        return 1
    except httpx.RequestError as e:
        print(f"❌ Error HTTP: {e}")
        return 1
    except Exception as e:
        print(f"❌ Error: {e}")
        if "CLOUDFLARE_API_TOKEN" in str(e):
            print("\nConfigura el token API:")
            print("  $env:CLOUDFLARE_API_TOKEN = 'tu-token-aqui'")
        return 1


if __name__ == "__main__":
    sys.exit(main())
