"""Asynchronous HTTP client orchestrating DGII integrations."""
from __future__ import annotations

import asyncio
import hashlib
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Awaitable, Callable, Dict, Optional

import httpx
from httpx import AsyncClient, HTTPError, HTTPStatusError
from lxml import etree

from app.core.logging import bind_request_context
from app.dgii.exceptions import DGIIAuthError, DGIIReceiptError, DGIIRetryableError
from app.dgii.retry import async_retry
from app.dgii.signing import sign_ecf
from app.infra.settings import Settings, settings


@dataclass(slots=True)
class CachedToken:
    access_token: str
    expires_at: datetime

    @property
    def is_valid(self) -> bool:
        return self.expires_at - timedelta(seconds=30) > datetime.now(timezone.utc)


class _IdempotencyCache:
    """Lightweight in-memory cache for DGII submissions."""

    def __init__(self) -> None:
        self._records: Dict[str, Dict[str, Any]] = {}
        self._lock = asyncio.Lock()

    async def get(self, key: str, payload_hash: str) -> Optional[Dict[str, Any]]:
        async with self._lock:
            record = self._records.get(key)
            if not record:
                return None
            if record["payload_hash"] != payload_hash:
                raise DGIIReceiptError("Payload distinto para el mismo Idempotency-Key")
            return record["body"]

    async def set(self, key: str, payload_hash: str, body: Dict[str, Any]) -> None:
        async with self._lock:
            self._records[key] = {
                "payload_hash": payload_hash,
                "body": body,
                "stored_at": datetime.now(timezone.utc),
            }


class _ConfigAdapter:
    def __init__(self, raw: Any):
        self.raw = raw

    def _get(self, attr: str, default: Any) -> Any:
        return getattr(self.raw, attr, default)

    @property
    def dgii_timeout(self) -> float:
        return float(self._get("dgii_timeout", self._get("dgii_http_timeout_seconds", 30.0)))

    @property
    def dgii_conn_timeout(self) -> float:
        return float(self._get("dgii_conn_timeout", 5.0))

    @property
    def dgii_max_retries(self) -> int:
        return int(self._get("dgii_max_retries", self._get("dgii_http_retries", 3)))

    @property
    def dgii_circuit_breaker_threshold(self) -> int:
        return int(self._get("dgii_circuit_breaker_threshold", 5))

    @property
    def dgii_circuit_breaker_window(self) -> int:
        return int(self._get("dgii_circuit_breaker_window", 60))

    @property
    def dgii_p12_path(self) -> Path:
        value = self._get("dgii_p12_path", self._get("dgii_cert_p12_path", Path("/secrets/cert.p12")))
        return Path(value)

    @property
    def dgii_p12_password(self) -> str:
        return self._get("dgii_p12_password", self._get("dgii_cert_p12_password", "changeit"))

    @property
    def dgii_auth_base_url(self) -> str:
        try:
            return str(self.raw.dgii_auth_base_url)
        except AttributeError:
            env = getattr(self.raw, "dgii_env", "PRECERT")
            if env == "CERT":
                return str(getattr(self.raw, "dgii_auth_base_url_cert", ""))
            if env == "PROD":
                return str(getattr(self.raw, "dgii_auth_base_url_prod", ""))
            return str(getattr(self.raw, "dgii_auth_base_url_precert", ""))

    @property
    def dgii_recepcion_base_url(self) -> str:
        try:
            return str(self.raw.dgii_recepcion_base_url)
        except AttributeError:
            env = getattr(self.raw, "dgii_env", "PRECERT")
            if env == "CERT":
                return str(getattr(self.raw, "dgii_recepcion_base_url_cert", ""))
            if env == "PROD":
                return str(getattr(self.raw, "dgii_recepcion_base_url_prod", ""))
            return str(getattr(self.raw, "dgii_recepcion_base_url_precert", ""))

    @property
    def dgii_recepcion_fc_base_url(self) -> str:
        try:
            return str(self.raw.dgii_recepcion_fc_base_url)
        except AttributeError:
            env = getattr(self.raw, "dgii_env", "PRECERT")
            if env == "CERT":
                return str(getattr(self.raw, "dgii_recepcion_fc_base_url_cert", ""))
            if env == "PROD":
                return str(getattr(self.raw, "dgii_recepcion_fc_base_url_prod", ""))
            return str(getattr(self.raw, "dgii_recepcion_fc_base_url_precert", ""))

    @property
    def dgii_directorio_base_url(self) -> str:
        if hasattr(self.raw, "dgii_directorio_base_url"):
            return str(self.raw.dgii_directorio_base_url)
        env = getattr(self.raw, "dgii_env", "PRECERT")
        if env == "CERT":
            return str(getattr(self.raw, "dgii_consulta_directorio_base_url_cert", getattr(self.raw, "dgii_consulta_directorio_base_url_precert", "")))
        if env == "PROD":
            return str(getattr(self.raw, "dgii_consulta_directorio_base_url_prod", getattr(self.raw, "dgii_consulta_directorio_base_url_precert", "")))
        return str(getattr(self.raw, "dgii_consulta_directorio_base_url_precert", ""))


class DGIIClient:
    """High-level client implementing semilla→token→envíos with resiliency."""

    def __init__(
        self,
        *,
        config: Settings | None = None,
        client: AsyncClient | None = None,
    ) -> None:
        self.config = config or settings
        self._cfg = _ConfigAdapter(self.config)
        timeout = httpx.Timeout(self._cfg.dgii_timeout, connect=self._cfg.dgii_conn_timeout)
        self._client = client or AsyncClient(timeout=timeout)
        self._own_client = client is None
        self._auth_base = self._cfg.dgii_auth_base_url
        self._recepcion_base = self._cfg.dgii_recepcion_base_url
        self._recepcion_fc_base = self._cfg.dgii_recepcion_fc_base_url
        self._directorio_base = self._cfg.dgii_directorio_base_url
        self._token: CachedToken | None = None
        self._token_lock = asyncio.Lock()
        self._idempotency_cache = _IdempotencyCache()
        self._failure_count = 0
        self._breaker_until: datetime | None = None

    async def __aenter__(self) -> "DGIIClient":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.close()

    async def close(self) -> None:
        if self._own_client:
            await self._client.aclose()

    async def bearer(self, *, force_refresh: bool = False) -> str:
        """Return a cached DGII token, refreshing when necessary."""

        async with self._token_lock:
            if not force_refresh and self._token and self._token.is_valid:
                return self._token.access_token
            seed = await self.get_seed()
            signed_seed = self.sign_seed(seed)
            token_payload = await self.get_token(signed_seed)
            expires_at = self._parse_expiration(token_payload["expires_at"])
            self._token = CachedToken(access_token=token_payload["access_token"], expires_at=expires_at)
            return self._token.access_token

    async def get_seed(self) -> bytes:
        url = f"{self._auth_base}/semilla"
        response = await self._request("GET", url)
        return response.content

    def sign_seed(self, seed_xml: bytes) -> bytes:
        return sign_ecf(seed_xml, str(self._cfg.dgii_p12_path), self._cfg.dgii_p12_password)

    async def get_token(self, signed_seed_xml: bytes) -> Dict[str, Any]:
        url = f"{self._auth_base}/token"
        response = await self._request(
            "POST",
            url,
            content=signed_seed_xml,
            headers={"Content-Type": "application/xml"},
        )
        try:
            payload = response.json()
        except ValueError as exc:
            raise DGIIAuthError("Respuesta inválida al obtener token") from exc

        token = payload.get("access_token") or payload.get("token")
        expires = payload.get("expires_at") or payload.get("expiration")
        if not token or not expires:
            raise DGIIAuthError("La respuesta de token no contiene campos requeridos")
        return {"access_token": token, "expires_at": expires}

    async def send_ecf(
        self,
        xml_bytes: bytes,
        *,
        token: str | None = None,
        idempotency_key: str | None = None,
        reutilizar_encf: bool = False,
        usage_callback: Callable[[Dict[str, Any]], Awaitable[None]] | None = None,
    ) -> Dict[str, Any]:
        payload = await self._submit(
            f"{self._recepcion_base}/ecf",
            xml_bytes,
            token=token,
            idempotency_key=idempotency_key,
            extra_headers={"X-Reutilizar-ENCF": "true"} if reutilizar_encf else None,
        )
        if usage_callback:
            await usage_callback(payload)
        return payload

    async def send_rfce(
        self,
        xml_bytes: bytes,
        *,
        token: str | None = None,
        idempotency_key: str | None = None,
    ) -> Dict[str, Any]:
        return await self._submit(
            f"{self._recepcion_fc_base}/rfce",
            xml_bytes,
            token=token,
            idempotency_key=idempotency_key,
        )

    async def send_anecf(
        self,
        xml_bytes: bytes,
        *,
        token: str | None = None,
        idempotency_key: str | None = None,
    ) -> Dict[str, Any]:
        return await self._submit(
            f"{self._recepcion_base}/anecf",
            xml_bytes,
            token=token,
            idempotency_key=idempotency_key,
        )

    async def send_acecf(
        self,
        xml_bytes: bytes,
        *,
        token: str | None = None,
        idempotency_key: str | None = None,
    ) -> Dict[str, Any]:
        return await self._submit(
            f"{self._recepcion_base}/acecf",
            xml_bytes,
            token=token,
            idempotency_key=idempotency_key,
        )

    async def send_arecf(
        self,
        xml_bytes: bytes,
        *,
        token: str | None = None,
        idempotency_key: str | None = None,
    ) -> Dict[str, Any]:
        return await self._submit(
            f"{self._recepcion_base}/arecef",
            xml_bytes,
            token=token,
            idempotency_key=idempotency_key,
        )

    async def consulta_directorio(self, rnc: str, token: str | None = None) -> Dict[str, Any]:
        auth_token = token or await self.bearer()
        url = f"{self._directorio_base}/rnc/{rnc}"
        response = await self._request("GET", url, headers=self._auth_headers(auth_token))
        return self._parse_payload(response)

    async def consulta_resumen(self, *, desde: str, hasta: str, token: str | None = None) -> Dict[str, Any]:
        auth_token = token or await self.bearer()
        url = f"{self._recepcion_fc_base}/resumen"
        response = await self._request(
            "GET",
            url,
            headers=self._auth_headers(auth_token),
            params={"desde": desde, "hasta": hasta},
        )
        return self._parse_payload(response)

    async def consulta_trackid(self, track_id: str, token: str | None = None) -> Dict[str, Any]:
        return await self.get_status(track_id, token=token)

    async def consulta_resultado(self, track_id: str, token: str | None = None) -> Dict[str, Any]:
        auth_token = token or await self.bearer()
        url = f"{self._recepcion_base}/resultado/{track_id}"
        response = await self._request("GET", url, headers=self._auth_headers(auth_token))
        return self._parse_payload(response)

    async def get_status(self, track_id: str, token: str | None = None) -> Dict[str, Any]:
        auth_token = token or await self.bearer()
        url = f"{self._recepcion_base}/estatus/{track_id}"
        response = await self._request("GET", url, headers=self._auth_headers(auth_token))
        return self._parse_payload(response)

    async def _submit(
        self,
        url: str,
        xml_bytes: bytes,
        *,
        token: str | None,
        idempotency_key: str | None,
        extra_headers: Dict[str, str] | None = None,
    ) -> Dict[str, Any]:
        auth_token = token or await self.bearer()
        payload_hash = hashlib.sha256(xml_bytes).hexdigest()
        cache_key = idempotency_key or str(uuid.uuid4())
        cached = await self._idempotency_cache.get(cache_key, payload_hash)
        if cached:
            return cached

        headers = {"Content-Type": "application/xml", **self._auth_headers(auth_token), "Idempotency-Key": cache_key}
        if extra_headers:
            headers.update(extra_headers)
        response = await self._request("POST", url, content=xml_bytes, headers=headers)
        payload = self._parse_payload(response)
        await self._idempotency_cache.set(cache_key, payload_hash, payload)
        return payload

    async def _request(
        self,
        method: str,
        url: str,
        *,
        headers: Optional[Dict[str, str]] = None,
        content: bytes | None = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> httpx.Response:
        self._ensure_breaker_available()
        self._ensure_allowed_host(url)
        logger = bind_request_context(url=url, method=method)
        retries = self._cfg.dgii_max_retries
        async for attempt in async_retry(retries):
            with attempt:
                try:
                    response = await self._client.request(
                        method,
                        url,
                        headers=headers,
                        content=content,
                        params=params,
                    )
                    response.raise_for_status()
                    self._reset_breaker()
                    logger.info("DGII HTTP OK", status_code=response.status_code)
                    return response
                except HTTPStatusError as exc:
                    self._register_failure()
                    status_code = exc.response.status_code
                    body = exc.response.text
                    logger.warning("DGII HTTP error", status_code=status_code, body=body[:250])
                    if 400 <= status_code < 500:
                        raise DGIIReceiptError(f"DGII rechazó la solicitud ({status_code})") from exc
                    raise
                except HTTPError as exc:
                    self._register_failure()
                    logger.warning("DGII HTTP transitorio", error=str(exc))
                    raise DGIIRetryableError("Error de comunicación con DGII") from exc

        raise RuntimeError("Reintentos agotados para llamada DGII")  # pragma: no cover

    def _ensure_allowed_host(self, url: str) -> None:
        parsed = httpx.URL(url)
        host = parsed.host
        if not host or host not in self.config.dgii_allowed_hosts:
            raise DGIIRetryableError("Host no permitido para DGII")

    def _auth_headers(self, token: str) -> Dict[str, str]:
        return {"Authorization": f"Bearer {token}"}

    def _parse_payload(self, response: httpx.Response) -> Dict[str, Any]:
        if response.headers.get("Content-Type", "").startswith("application/xml"):
            return self._parse_xml_payload(response.content)
        try:
            return response.json()
        except ValueError:
            return {"raw": response.text}

    def _parse_xml_payload(self, content: bytes) -> Dict[str, Any]:
        try:
            root = etree.fromstring(content)
        except etree.XMLSyntaxError:
            return {"raw": content.decode("utf-8", "ignore")}
        payload: Dict[str, Any] = {}
        for child in root.iterchildren():
            payload[child.tag.lower()] = child.text
        return payload

    def _parse_expiration(self, value: str) -> datetime:
        sanitized = value.replace("Z", "+00:00")
        try:
            expires = datetime.fromisoformat(sanitized)
        except ValueError:
            expires = datetime.now(timezone.utc) + timedelta(minutes=10)
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
        return expires.astimezone(timezone.utc)

    def _ensure_breaker_available(self) -> None:
        if self._breaker_until and self._breaker_until > datetime.now(timezone.utc):
            raise DGIIRetryableError("Circuit breaker abierto para DGII")

    def _register_failure(self) -> None:
        self._failure_count += 1
        if self._failure_count >= self._cfg.dgii_circuit_breaker_threshold:
            self._breaker_until = datetime.now(timezone.utc) + timedelta(seconds=self._cfg.dgii_circuit_breaker_window)
            self._failure_count = 0

    def _reset_breaker(self) -> None:
        self._failure_count = 0
        self._breaker_until = None
