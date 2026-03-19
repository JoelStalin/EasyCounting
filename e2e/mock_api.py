from __future__ import annotations

import json
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Lock, Thread
from urllib.parse import parse_qs, urlparse


ADMIN_PERMISSIONS = [
    "PLATFORM_TENANT_VIEW",
    "PLATFORM_PLAN_CRUD",
    "PLATFORM_AUDIT_VIEW",
    "PLATFORM_USER_MANAGE",
    "PLATFORM_AI_PROVIDER_MANAGE",
]

TENANT_PERMISSIONS = [
    "TENANT_INVOICE_READ",
    "TENANT_INVOICE_EMIT",
    "TENANT_RFCE_SUBMIT",
    "TENANT_APPROVAL_SEND",
    "TENANT_CERT_UPLOAD",
    "TENANT_PLAN_VIEW",
    "TENANT_PLAN_UPGRADE",
    "TENANT_USAGE_VIEW",
    "TENANT_CHAT_ASSIST",
]

PARTNER_PERMISSIONS = [
    "PARTNER_DASHBOARD_VIEW",
    "PARTNER_TENANT_VIEW",
    "PARTNER_CLIENT_VIEW",
    "PARTNER_INVOICE_READ",
    "PARTNER_INVOICE_EMIT",
]


@dataclass
class MockState:
    tenants: list[dict[str, object]] = field(
        default_factory=lambda: [
            {
                "id": 1,
                "name": "Empresa Demo",
                "rnc": "13100000001",
                "env": "PRECERT",
                "status": "Activa",
            }
        ]
    )
    next_tenant_id: int = 2
    partner_invoices: list[dict[str, object]] = field(
        default_factory=lambda: [
            {
                "id": 9001,
                "tenantId": 1,
                "tenantName": "Empresa Demo",
                "encf": "E310000000099",
                "tipoEcf": "31",
                "estadoDgii": "ACEPTADO",
                "trackId": "partner-track-001",
                "total": "1500.00",
                "fechaEmision": "2026-03-18T12:00:00",
            }
        ]
    )
    next_partner_invoice_id: int = 9002
    lock: Lock = field(default_factory=Lock)

    def create_tenant(self, payload: dict[str, object]) -> dict[str, object]:
        with self.lock:
            tenant = {
                "id": self.next_tenant_id,
                "name": str(payload.get("name", "")),
                "rnc": str(payload.get("rnc", "")),
                "env": str(payload.get("env", "PRECERT")),
                "status": "Activa",
            }
            self.next_tenant_id += 1
            self.tenants.insert(0, tenant)
            return tenant

    def get_tenants(self) -> list[dict[str, object]]:
        with self.lock:
            return [tenant.copy() for tenant in self.tenants]

    def get_tenant(self, tenant_id: int) -> dict[str, object] | None:
        with self.lock:
            for tenant in self.tenants:
                if int(tenant["id"]) == tenant_id:
                    return tenant.copy()
        return None

    def get_partner_tenants(self) -> list[dict[str, object]]:
        with self.lock:
            return [
                {
                    "id": 1,
                    "name": "Empresa Demo",
                    "rnc": "13100000001",
                    "env": "PRECERT",
                    "status": "Activa",
                    "canEmit": True,
                    "canManage": True,
                    "invoiceCount": len(self.partner_invoices),
                    "totalAmount": "1500.00",
                },
                {
                    "id": 2,
                    "name": "Cliente Solo Lectura",
                    "rnc": "13100000002",
                    "env": "CERT",
                    "status": "Activa",
                    "canEmit": False,
                    "canManage": False,
                    "invoiceCount": 0,
                    "totalAmount": "0.00",
                },
            ]

    def get_partner_dashboard(self) -> dict[str, object]:
        items = self.get_partner_tenants()
        return {
            "partner": {
                "accountId": 1,
                "accountName": "Seller Demo",
                "accountSlug": "seller-demo",
                "userEmail": "seller@getupsoft.com.do",
                "role": "partner_reseller",
                "scope": "PARTNER",
            },
            "tenantCount": len(items),
            "invoiceCount": len(self.partner_invoices),
            "acceptedCount": sum(1 for item in self.partner_invoices if item["estadoDgii"] == "ACEPTADO"),
            "pendingCount": sum(1 for item in self.partner_invoices if item["estadoDgii"] != "ACEPTADO"),
            "totalAmount": "1500.00",
            "tenants": items,
        }

    def get_partner_profile(self, email: str, role: str) -> dict[str, object]:
        return {
            "accountId": 1,
            "accountName": "Seller Demo",
            "accountSlug": "seller-demo",
            "userEmail": email,
            "role": role,
            "scope": "PARTNER",
        }

    def list_partner_invoices(self, tenant_id: int | None = None) -> dict[str, object]:
        with self.lock:
            items = [invoice.copy() for invoice in self.partner_invoices if tenant_id is None or int(invoice["tenantId"]) == tenant_id]
        return {"items": items, "total": len(items), "page": 1, "size": 20}

    def emit_partner_invoice(self, payload: dict[str, object]) -> dict[str, object]:
        with self.lock:
            invoice = {
                "id": self.next_partner_invoice_id,
                "tenantId": int(payload.get("tenantId", 1)),
                "tenantName": "Empresa Demo",
                "encf": str(payload.get("encf", "")),
                "tipoEcf": str(payload.get("tipoEcf", "31")),
                "estadoDgii": "SIMULADO",
                "trackId": f"partner-track-{self.next_partner_invoice_id}",
                "total": str(payload.get("total", "0.00")),
                "fechaEmision": "2026-03-18T12:30:00",
            }
            self.next_partner_invoice_id += 1
            self.partner_invoices.insert(0, invoice)
        return {
            "invoiceId": invoice["id"],
            "tenantId": invoice["tenantId"],
            "encf": invoice["encf"],
            "estadoDgii": invoice["estadoDgii"],
            "trackId": invoice["trackId"],
            "total": invoice["total"],
            "message": "Comprobante seller generado en modo demo.",
        }


def _set_cors_headers(handler: BaseHTTPRequestHandler) -> None:
    origin = handler.headers.get("Origin", "http://127.0.0.1")
    handler.send_header("Access-Control-Allow-Origin", origin)
    handler.send_header("Access-Control-Allow-Credentials", "true")
    handler.send_header("Access-Control-Allow-Headers", "Authorization, Content-Type, X-Request-ID, X-Tenant-ID")
    handler.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, PATCH, DELETE, OPTIONS")


def _json_response(handler: BaseHTTPRequestHandler, status_code: int, payload: dict | list) -> None:
    body = json.dumps(payload).encode("utf-8")
    handler.send_response(status_code)
    _set_cors_headers(handler)
    handler.send_header("Content-Type", "application/json")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def _parse_body(handler: BaseHTTPRequestHandler) -> dict[str, object]:
    raw_length = handler.headers.get("Content-Length", "0")
    try:
        length = int(raw_length)
    except ValueError:
        length = 0
    if length <= 0:
        return {}
    raw = handler.rfile.read(length)
    if not raw:
        return {}
    return json.loads(raw.decode("utf-8"))


def _build_login_response(email: str) -> dict[str, object]:
    normalized = email.strip().lower()
    if normalized in {"admin@getupsoft.com.do", "admin"} or normalized.startswith("admin@"):
        return {
            "access_token": "platform-access-token",
            "refresh_token": "platform-refresh-token",
            "user": {
                "id": "1",
                "email": email.strip() or "admin@getupsoft.com.do",
                "scope": "PLATFORM",
                "tenant_id": None,
                "roles": ["platform_superroot"],
            },
            "permissions": ADMIN_PERMISSIONS,
            "mfa_required": False,
        }

    if normalized.startswith("seller"):
        role = "partner_auditor" if "auditor" in normalized else "partner_operator" if "operator" in normalized else "partner_reseller"
        permissions = [perm for perm in PARTNER_PERMISSIONS if perm != "PARTNER_INVOICE_EMIT"] if role == "partner_auditor" else PARTNER_PERMISSIONS
        return {
            "access_token": "partner-access-token",
            "refresh_token": "partner-refresh-token",
            "user": {
                "id": "3",
                "email": email.strip() or "seller@getupsoft.com.do",
                "scope": "PARTNER",
                "tenant_id": None,
                "roles": [role],
            },
            "permissions": permissions,
            "mfa_required": False,
        }

    return {
        "access_token": "tenant-access-token",
        "refresh_token": "tenant-refresh-token",
        "user": {
            "id": "2",
            "email": email.strip() or "cliente@getupsoft.com.do",
            "scope": "TENANT",
            "tenant_id": "1",
            "roles": ["tenant_admin"],
        },
        "permissions": TENANT_PERMISSIONS,
        "mfa_required": False,
    }


def _handler_for(state: MockState):
    class MockApiHandler(BaseHTTPRequestHandler):
        def log_message(self, format: str, *args) -> None:  # noqa: A003
            return

        def do_OPTIONS(self) -> None:  # noqa: N802
            self.send_response(204)
            _set_cors_headers(self)
            self.end_headers()

        def do_GET(self) -> None:  # noqa: N802
            parsed = urlparse(self.path)
            path = parsed.path
            if path == "/__health__":
                _json_response(self, 200, {"status": "ok"})
                return
            if path == "/api/v1/me":
                authorization = self.headers.get("Authorization", "")
                if "partner-access-token" in authorization:
                    _json_response(self, 200, _build_login_response("seller@getupsoft.com.do"))
                    return
                if "tenant-access-token" in authorization:
                    _json_response(self, 200, _build_login_response("cliente@getupsoft.com.do"))
                    return
                _json_response(self, 200, _build_login_response("admin@getupsoft.com.do"))
                return
            if path == "/api/v1/partner/me":
                role = "partner_auditor" if "seller.auditor" in self.headers.get("X-Demo-Email", "") else "partner_reseller"
                _json_response(self, 200, state.get_partner_profile("seller@getupsoft.com.do", role))
                return
            if path == "/api/v1/partner/dashboard":
                _json_response(self, 200, state.get_partner_dashboard())
                return
            if path == "/api/v1/partner/tenants":
                _json_response(self, 200, state.get_partner_tenants())
                return
            if path == "/api/v1/partner/invoices":
                tenant_param = parse_qs(parsed.query).get("tenant_id", [None])[0]
                tenant_id = int(tenant_param) if tenant_param else None
                _json_response(self, 200, state.list_partner_invoices(tenant_id))
                return
            if path == "/api/v1/admin/ai-providers":
                _json_response(self, 200, [])
                return
            if path == "/api/v1/admin/tenants":
                _json_response(self, 200, state.get_tenants())
                return
            if path.startswith("/api/v1/admin/tenants/"):
                tenant_id_str = path.removeprefix("/api/v1/admin/tenants/")
                if "/" in tenant_id_str:
                    tenant_id_str = tenant_id_str.split("/", 1)[0]
                try:
                    tenant_id = int(tenant_id_str)
                except ValueError:
                    _json_response(self, 404, {"detail": "tenant not found"})
                    return
                tenant = state.get_tenant(tenant_id)
                if not tenant:
                    _json_response(self, 404, {"detail": "tenant not found"})
                    return
                _json_response(self, 200, tenant)
                return
            _json_response(self, 404, {"detail": "not found"})

        def do_POST(self) -> None:  # noqa: N802
            path = urlparse(self.path).path
            payload = _parse_body(self)
            if path in {"/auth/login", "/api/v1/auth/login"}:
                password = str(payload.get("password", ""))
                if not password:
                    _json_response(self, 401, {"detail": "Credenciales invalidas"})
                    return
                _json_response(self, 200, _build_login_response(str(payload.get("email", ""))))
                return
            if path == "/api/v1/partner/emit":
                _json_response(self, 201, state.emit_partner_invoice(payload))
                return
            if path == "/api/v1/admin/tenants":
                _json_response(self, 200, state.create_tenant(payload))
                return
            _json_response(self, 404, {"detail": "not found"})

    return MockApiHandler


def start_mock_api_server(base_url: str) -> tuple[ThreadingHTTPServer, Thread]:
    parsed = urlparse(base_url)
    host = parsed.hostname or "127.0.0.1"
    port = int(parsed.port or 80)
    server = ThreadingHTTPServer((host, port), _handler_for(MockState()))
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, thread
