from __future__ import annotations

import base64

import httpx

from app.infra.settings import settings


class SecretStoreError(RuntimeError):
    pass


_LOCAL_SECRET_STORE: dict[str, dict] = {}


def store_certificate_secret(
    *,
    case_id: str,
    certificate_bytes: bytes,
    certificate_password: str,
    metadata: dict,
) -> str:
    provider = (settings.secret_provider or "env").strip().lower()
    payload = {
        "case_id": case_id,
        "certificate_base64": base64.b64encode(certificate_bytes).decode("utf-8"),
        "certificate_password": certificate_password,
        "metadata": metadata,
    }
    if provider == "vault":
        if not settings.vault_addr or not settings.vault_token:
            raise SecretStoreError("VAULT_ADDR/VAULT_TOKEN no configurados")
        base = str(settings.vault_addr).rstrip("/")
        path = f"{settings.vault_cert_secret_prefix.strip('/').strip()}/{case_id}".strip("/")
        url = f"{base}/v1/{path}"
        response = httpx.post(
            url,
            headers={"X-Vault-Token": settings.vault_token},
            json={"data": payload},
            timeout=15.0,
        )
        if response.status_code >= 400:
            raise SecretStoreError(f"Vault rejected secret write: {response.status_code}")
        return f"vault://{path}"

    ref = f"env://certificate-workflow/{case_id}"
    _LOCAL_SECRET_STORE[ref] = payload
    return ref


def load_certificate_secret(secret_ref: str) -> dict:
    ref = (secret_ref or "").strip()
    if not ref:
        raise SecretStoreError("secret_ref vacio")
    if ref.startswith("vault://"):
        if not settings.vault_addr or not settings.vault_token:
            raise SecretStoreError("VAULT_ADDR/VAULT_TOKEN no configurados")
        path = ref.replace("vault://", "", 1).strip("/")
        base = str(settings.vault_addr).rstrip("/")
        url = f"{base}/v1/{path}"
        response = httpx.get(url, headers={"X-Vault-Token": settings.vault_token}, timeout=15.0)
        if response.status_code >= 400:
            raise SecretStoreError(f"Vault rejected secret read: {response.status_code}")
        body = response.json()
        data = body.get("data", {})
        if isinstance(data, dict) and "data" in data and isinstance(data["data"], dict):
            return data["data"]
        if isinstance(data, dict):
            return data
        raise SecretStoreError("Vault payload invalido")
    if ref.startswith("env://"):
        payload = _LOCAL_SECRET_STORE.get(ref)
        if payload is None:
            raise SecretStoreError("No existe secreto en store local para el secret_ref indicado")
        return payload
    raise SecretStoreError("Formato de secret_ref no soportado")
