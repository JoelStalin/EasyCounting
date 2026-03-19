"""Authentication helpers for the DGII portal."""

from __future__ import annotations

import re
from typing import Any

from app.dgii_portal_automation.errors import (
    DGIIAuthenticationError,
    DGIIHumanActionRequired,
    DGIISessionError,
)
from app.dgii_portal_automation.navigation import wait_for_page_ready
from app.dgii_portal_automation.safety import safe_logging
from app.dgii_portal_automation.ui import find_clickable, find_input

LOGIN_HINTS = ("usuario", "correo", "email", "rnc", "cedula", "documento")
PASSWORD_HINTS = ("contrasena", "clave", "password", "pin")
SUBMIT_HINTS = ("entrar", "acceder", "iniciar sesion", "continuar", "login")
LOGOUT_HINTS = ("cerrar sesion", "salir", "logout")
MFA_HINTS = ("codigo", "token", "verificacion", "mfa", "otp")
CAPTCHA_HINTS = ("captcha", "recaptcha", "robot", "human verification")


def login(runtime: Any) -> str:
    runtime.config.ensure_credentials()
    page = runtime.ensure_page()
    runtime.ensure_authorized_url(runtime.config.login_url)
    page.goto(runtime.config.login_url, wait_until="domcontentloaded")
    wait_for_page_ready(runtime)

    user_input = find_input(page, *LOGIN_HINTS)
    password_input = find_input(page, *PASSWORD_HINTS, prefer_password=True)
    submit_button = find_clickable(page, *SUBMIT_HINTS)

    if user_input is None or password_input is None or submit_button is None:
        raise DGIIAuthenticationError("No se pudo resolver el formulario de autenticacion de forma segura")

    user_input.fill(runtime.config.username or "", timeout=runtime.config.action_timeout_ms)
    password_input.fill(runtime.config.password or "", timeout=runtime.config.action_timeout_ms)
    safe_logging(runtime, "auth.form_filled", level="info", url=page.url)
    submit_button.click(timeout=runtime.config.action_timeout_ms)
    wait_for_page_ready(runtime, extra_wait_ms=800)

    if _has_human_challenge(page):
        raise DGIIHumanActionRequired("La pagina requiere una accion humana adicional (captcha, MFA o challenge)")
    if _shows_login_form(page):
        raise DGIIAuthenticationError("El portal sigue mostrando el formulario de login despues del envio")

    safe_logging(runtime, "auth.login.success", level="info", url=page.url)
    return page.url


def validate_session(runtime: Any) -> bool:
    page = runtime.ensure_page()
    current = page.url or runtime.config.base_url
    runtime.ensure_authorized_url(current)
    try:
        page.locator("body").wait_for(state="visible", timeout=runtime.config.action_timeout_ms)
    except Exception as exc:  # pragma: no cover - defensive
        raise DGIISessionError("No se pudo validar la sesion actual") from exc
    valid = not _shows_login_form(page)
    safe_logging(runtime, "auth.session.validated", level="info", valid=valid, url=page.url)
    return valid


def refresh_session(runtime: Any) -> str:
    page = runtime.ensure_page()
    if validate_session(runtime):
        return page.url
    safe_logging(runtime, "auth.session.refresh", level="warning", url=page.url)
    return login(runtime)


def logout(runtime: Any) -> None:
    page = runtime.ensure_page()
    logout_button = find_clickable(page, *LOGOUT_HINTS)
    if logout_button is not None:
        logout_button.click(timeout=runtime.config.action_timeout_ms)
        wait_for_page_ready(runtime, extra_wait_ms=600)
    runtime.context.clear_cookies()
    safe_logging(runtime, "auth.logout", level="info", url=page.url)


def _shows_login_form(page: Any) -> bool:
    return find_input(page, *LOGIN_HINTS) is not None and find_input(page, *PASSWORD_HINTS, prefer_password=True) is not None


def _has_human_challenge(page: Any) -> bool:
    body_text = ""
    try:
        body_text = page.locator("body").inner_text(timeout=3000)
    except Exception:
        return False
    lowered = body_text.lower()
    if any(term in lowered for term in CAPTCHA_HINTS):
        return True
    if any(term in lowered for term in MFA_HINTS):
        password_input = find_input(page, *PASSWORD_HINTS, prefer_password=True)
        if password_input is None or not password_input.is_visible():
            return True
    iframe_count = page.locator("iframe").count()
    for index in range(min(iframe_count, 20)):
        frame = page.locator("iframe").nth(index)
        try:
            title = (frame.get_attribute("title") or "") + " " + (frame.get_attribute("name") or "")
        except Exception:
            title = ""
        if re.search(r"captcha|recaptcha|challenge", title, re.IGNORECASE):
            return True
    return False
