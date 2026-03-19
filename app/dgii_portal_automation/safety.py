"""Safety layer: secret redaction, action gating and safe evidence capture."""

from __future__ import annotations

from dataclasses import asdict
import json
import re
import sys
from pathlib import Path
from typing import Any, Callable
from urllib.parse import urlparse

from PIL import Image, ImageFilter

from app.dgii_portal_automation.config import ExecutionMode
from app.dgii_portal_automation.errors import DGIIHumanActionRequired, DGIISensitiveActionBlockedError
from app.dgii_portal_automation.models import SensitiveAction

SENSITIVE_PATTERNS: dict[str, tuple[str, str]] = {
    "declarar": ("declaracion", "La accion parece iniciar o enviar una declaracion tributaria."),
    "enviar": ("envio", "La accion parece remitir informacion formal a la DGII."),
    "rectificar": ("rectificacion", "La accion parece rectificar informacion presentada."),
    "pagar": ("pago", "La accion parece iniciar un pago o autorizacion economica."),
    "confirmar": ("confirmacion", "La accion parece confirmar una operacion irreversible."),
    "firmar": ("firma", "La accion parece requerir firma o consentimiento formal."),
    "presentar": ("presentacion", "La accion parece presentar informacion con impacto legal."),
    "someter": ("presentacion", "La accion parece someter informacion oficial."),
}

READ_ONLY_SAFE_TERMS = {"consultar", "buscar", "ver", "descargar", "exportar", "filtrar", "siguiente", "anterior"}


def detect_sensitive_action(
    label: str | None,
    *,
    current_url: str | None = None,
    details: dict[str, Any] | None = None,
) -> SensitiveAction | None:
    text = " ".join(filter(None, [label or "", current_url or "", json.dumps(details or {}, ensure_ascii=False)]))
    lowered = text.lower()
    if any(term in lowered for term in READ_ONLY_SAFE_TERMS):
        return None
    for needle, (action_type, reason) in SENSITIVE_PATTERNS.items():
        if needle in lowered:
            return SensitiveAction(
                action_type=action_type,
                label=label or needle,
                reason=reason,
                risk="alto",
                current_url=current_url,
                details=details or {},
            )
    return None


def request_confirmation(
    action: SensitiveAction,
    *,
    mode: ExecutionMode,
    confirmation_callback: Callable[[SensitiveAction], bool] | None = None,
) -> bool:
    if mode is ExecutionMode.READ_ONLY:
        raise DGIISensitiveActionBlockedError(
            f"Accion sensible bloqueada en modo solo lectura: {action.label} ({action.reason})"
        )
    if confirmation_callback is not None:
        approved = bool(confirmation_callback(action))
    elif sys.stdin.isatty():
        print(
            "\n".join(
                [
                    "Accion sensible detectada.",
                    f"Tipo: {action.action_type}",
                    f"Etiqueta: {action.label}",
                    f"Riesgo: {action.risk}",
                    f"Motivo: {action.reason}",
                    f"URL: {action.current_url or 'N/D'}",
                    "Escriba SI para continuar:",
                ]
            )
        )
        approved = input().strip().upper() == "SI"
    else:
        raise DGIIHumanActionRequired("Se requiere confirmacion humana para la accion sensible detectada")
    if not approved:
        raise DGIIHumanActionRequired("La accion sensible fue cancelada por falta de autorizacion explicita")
    return True


def redact_secrets(value: Any, *, secrets: list[str] | None = None) -> Any:
    secrets = [secret for secret in (secrets or []) if secret]
    if isinstance(value, dict):
        return {key: redact_secrets(item, secrets=secrets) for key, item in value.items()}
    if isinstance(value, list):
        return [redact_secrets(item, secrets=secrets) for item in value]
    if isinstance(value, tuple):
        return tuple(redact_secrets(item, secrets=secrets) for item in value)
    if not isinstance(value, str):
        return value
    redacted = value
    for secret in secrets:
        redacted = redacted.replace(secret, "***REDACTED***")
    redacted = re.sub(r"(Bearer\s+)[A-Za-z0-9._\-]+", r"\1***REDACTED***", redacted, flags=re.IGNORECASE)
    redacted = re.sub(r"(Cookie:\s*)(.+)", r"\1***REDACTED***", redacted, flags=re.IGNORECASE)
    redacted = re.sub(r"(token=)[^&\s]+", r"\1***REDACTED***", redacted, flags=re.IGNORECASE)
    return redacted


def safe_logging(runtime: Any, event: str, *, level: str = "info", **details: Any) -> None:
    secrets = [
        getattr(runtime.config, "username", None),
        getattr(runtime.config, "password", None),
    ]
    sanitized = redact_secrets(details, secrets=[item for item in secrets if item])
    runtime.record_event(event, level=level, **sanitized)


def safe_screenshot(page: Any, output_path: str | Path, *, runtime: Any, note: str | None = None) -> Path:
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    raw_path = destination.with_suffix(".raw.png")
    page.screenshot(path=str(raw_path), full_page=True)
    image = Image.open(raw_path)
    for locator in _locators_to_blur(page):
        try:
            box = locator.bounding_box()
        except Exception:
            box = None
        if not box:
            continue
        left = max(int(box["x"]), 0)
        top = max(int(box["y"]), 0)
        right = max(int(box["x"] + box["width"]), left + 1)
        bottom = max(int(box["y"] + box["height"]), top + 1)
        region = image.crop((left, top, right, bottom)).filter(
            ImageFilter.GaussianBlur(radius=runtime.config.screenshot_blur_radius)
        )
        image.paste(region, (left, top, right, bottom))
    image.save(destination)
    raw_path.unlink(missing_ok=True)
    safe_logging(runtime, "screenshot.saved", level="info", path=str(destination), note=note, url=page.url)
    return destination


def ensure_authorized_domain(url: str, *, allowed_domains: tuple[str, ...]) -> str:
    host = (urlparse(url).hostname or "").lower()
    if not host or not any(host == domain or host.endswith(f".{domain}") for domain in allowed_domains):
        raise DGIISensitiveActionBlockedError(f"URL fuera de dominio autorizado: {url}")
    return url


def summarize_sensitive_action(action: SensitiveAction) -> dict[str, Any]:
    return asdict(action)


def _locators_to_blur(page: Any) -> list[Any]:
    selectors = [
        "input[type='password']",
        "input[autocomplete='current-password']",
        "input[name*='token' i]",
        "input[name*='clave' i]",
        "textarea[name*='token' i]",
    ]
    locators: list[Any] = []
    for selector in selectors:
        locator = page.locator(selector)
        try:
            count = min(locator.count(), 20)
        except Exception:
            continue
        for index in range(count):
            item = locator.nth(index)
            try:
                if item.is_visible():
                    locators.append(item)
            except Exception:
                continue
    return locators
