"""HTTP client hardened against SSRF with retry and circuit breaker."""
from __future__ import annotations

import ipaddress
import socket
import time
from collections import defaultdict
from typing import Any, Dict, Optional

import httpx
from tenacity import AsyncRetrying, RetryError, retry_if_exception_type, stop_after_attempt, wait_exponential_jitter

from app.infra.settings import settings

_circuit_breaker: Dict[str, Dict[str, float]] = defaultdict(lambda: {"failures": 0, "opened_at": 0.0})


class SSRFProtectionError(RuntimeError):
    """Raised when a request violates SSRF protections."""


def _resolve_public_host(host: str) -> None:
    try:
        infos = socket.getaddrinfo(host, None)
    except socket.gaierror as exc:
        raise SSRFProtectionError("DNS resolution failed") from exc

    for _family, _type, _proto, _canonname, sockaddr in infos:
        ip = ipaddress.ip_address(sockaddr[0])
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_multicast or ip.is_reserved:
            raise SSRFProtectionError("Host resolves to a non-public address")


def _ensure_allowed(url: httpx.URL) -> None:
    host = url.host
    if not host or host not in settings.dgii_allowed_hosts:
        raise SSRFProtectionError("Host not in DGII allow-list")
    _resolve_public_host(host)


async def _request(method: str, url: str, **kwargs) -> httpx.Response:
    parsed_url = httpx.URL(url)
    _ensure_allowed(parsed_url)

    circuit = _circuit_breaker[parsed_url.host]
    if circuit["failures"] >= settings.dgii_circuit_breaker_threshold:
        if time.time() - circuit["opened_at"] < settings.dgii_circuit_breaker_window:
            raise RuntimeError("Circuit breaker open")
        circuit["failures"] = 0

    async for attempt in AsyncRetrying(
        retry=retry_if_exception_type(httpx.HTTPError),
        stop=stop_after_attempt(settings.dgii_max_retries),
        wait=wait_exponential_jitter(initial=0.5, max=settings.dgii_timeout),
        reraise=True,
    ):
        with attempt:
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(settings.dgii_timeout, connect=settings.dgii_conn_timeout),
                follow_redirects=False,
            ) as client:
                response = await client.request(method, url, **kwargs)
                response.raise_for_status()
                circuit["failures"] = 0
                return response

    raise RuntimeError("Unexpected retry exhaustion")


async def post_xml(url: str, data: bytes, headers: dict[str, str]) -> httpx.Response:
    try:
        return await _request("POST", url, content=data, headers=headers)
    except RetryError as exc:
        circuit = _circuit_breaker[httpx.URL(url).host]
        circuit["failures"] += 1
        circuit["opened_at"] = time.time()
        raise RuntimeError("DGII service unavailable") from exc


async def post_multipart(url: str, *, files: dict[str, Any], headers: dict[str, str]) -> httpx.Response:
    try:
        return await _request("POST", url, files=files, headers=headers)
    except RetryError as exc:
        circuit = _circuit_breaker[httpx.URL(url).host]
        circuit["failures"] += 1
        circuit["opened_at"] = time.time()
        raise RuntimeError("DGII service unavailable") from exc


async def get_json(url: str, headers: dict[str, str], *, params: Optional[dict[str, Any]] = None) -> httpx.Response:
    try:
        return await _request("GET", url, headers=headers, params=params)
    except RetryError as exc:
        circuit = _circuit_breaker[httpx.URL(url).host]
        circuit["failures"] += 1
        circuit["opened_at"] = time.time()
        raise RuntimeError("DGII status unavailable") from exc
