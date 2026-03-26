#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


DEFAULT_CERT_PORTAL_URL = "https://ecf.dgii.gov.do/certecf/PortalCertificacion/"
PROJECT_ROOT = Path(__file__).resolve().parents[2]
ARTIFACTS_ROOT = PROJECT_ROOT / "tests" / "artifacts"

KNOWN_STEP_LABELS = [
    "Registrado",
    "Pruebas de Datos e-CF",
    "Pruebas de Datos Aprobación Comercial",
    "Pruebas Simulación e-CF",
    "Pruebas Simulación Representación Impresa",
    "Validación Representación Impresa",
    "URL Servicios Prueba",
    "Inicio Prueba Recepción e-CF",
    "Recepción e-CF",
    "Inicio Prueba Recepción Aprobación Comercial",
    "Recepción Aprobación Comercial",
    "URL Servicios Producción",
    "Declaración Jurada",
    "Verificación Estatus",
    "Finalizado",
]


@dataclass(slots=True)
class PortalState:
    timestamp: str
    url: str
    title: str
    authenticated: bool
    current_step: str | None
    visible_steps: list[str]
    visible_buttons: list[str]
    visible_links: list[str]
    visible_inputs: list[str]


def _timestamp() -> str:
    return datetime.now().strftime("%Y-%m-%d_%H-%M-%S")


def _normalize(text: str) -> str:
    return " ".join(text.replace("\u00a0", " ").split())


def _safe_name(text: str) -> str:
    cleaned = "".join(ch if ch.isalnum() or ch in "-._" else "_" for ch in text.strip())
    return cleaned[:80] or "artifact"


def build_artifact_dir() -> Path:
    path = ARTIFACTS_ROOT / f"{_timestamp()}_dgii_cert_portal_real"
    path.mkdir(parents=True, exist_ok=True)
    return path


def configure_driver() -> webdriver.Chrome:
    options = Options()
    options.add_argument("--window-size=1440,1400")
    options.add_argument("--start-maximized")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    return webdriver.Chrome(options=options)


def capture(driver: webdriver.Chrome, run_dir: Path, label: str) -> PortalState:
    stamp = _timestamp()
    prefix = run_dir / f"{stamp}_{_safe_name(label)}"
    screenshot_path = prefix.with_suffix(".png")
    html_path = prefix.with_suffix(".html")
    json_path = prefix.with_suffix(".json")

    driver.save_screenshot(str(screenshot_path))
    html_path.write_text(driver.page_source, encoding="utf-8")

    state = read_state(driver)
    json_path.write_text(json.dumps(asdict(state), ensure_ascii=False, indent=2), encoding="utf-8")
    return state


def read_state(driver: webdriver.Chrome) -> PortalState:
    page_text = _normalize(driver.find_element(By.TAG_NAME, "body").text)
    visible_steps = [label for label in KNOWN_STEP_LABELS if label.lower() in page_text.lower()]
    current_step = next((label for label in visible_steps if f" {label} " in f" {page_text} "), None)

    buttons = []
    for element in driver.find_elements(By.CSS_SELECTOR, "button, input[type='submit'], input[type='button'], a.btn"):
        text = _normalize(element.text or element.get_attribute("value") or "")
        if text and text not in buttons:
            buttons.append(text)

    links = []
    for element in driver.find_elements(By.CSS_SELECTOR, "a"):
        text = _normalize(element.text)
        if text and len(text) <= 120 and text not in links:
            links.append(text)

    inputs = []
    for element in driver.find_elements(By.CSS_SELECTOR, "input, textarea, select"):
        name = _normalize(
            element.get_attribute("name")
            or element.get_attribute("id")
            or element.get_attribute("placeholder")
            or ""
        )
        if name and name not in inputs:
            inputs.append(name)

    authenticated = "/Login" not in (driver.current_url or "") and any(step in page_text for step in KNOWN_STEP_LABELS)
    return PortalState(
        timestamp=datetime.now().isoformat(),
        url=driver.current_url,
        title=driver.title,
        authenticated=authenticated,
        current_step=current_step,
        visible_steps=visible_steps,
        visible_buttons=buttons[:50],
        visible_links=links[:80],
        visible_inputs=inputs[:80],
    )


def try_fill_login(driver: webdriver.Chrome) -> bool:
    username = os.getenv("DGII_PORTAL_USERNAME", "").strip()
    password = os.getenv("DGII_PORTAL_PASSWORD", "").strip()
    if not username or not password:
        return False

    user_candidates = [
        (By.NAME, "RncCedula"),
        (By.NAME, "Usuario"),
        (By.NAME, "username"),
        (By.ID, "RncCedula"),
        (By.ID, "Usuario"),
    ]
    pass_candidates = [
        (By.NAME, "Clave"),
        (By.NAME, "Password"),
        (By.NAME, "password"),
        (By.ID, "Clave"),
        (By.ID, "Password"),
    ]

    user_input = _find_first(driver, user_candidates)
    password_input = _find_first(driver, pass_candidates)
    if user_input is None or password_input is None:
        return False

    user_input.clear()
    user_input.send_keys(username)
    password_input.clear()
    password_input.send_keys(password)

    for locator in [
        (By.CSS_SELECTOR, "button[type='submit']"),
        (By.CSS_SELECTOR, "input[type='submit']"),
        (By.XPATH, "//button[contains(., 'Entrar') or contains(., 'Acceder') or contains(., 'Iniciar')]"),
        (By.XPATH, "//input[@value='Entrar' or @value='Acceder' or @value='Iniciar sesión']"),
    ]:
        submit = _find_first(driver, [locator])
        if submit is not None:
            submit.click()
            return True
    return False


def _find_first(driver: webdriver.Chrome, locators: list[tuple[str, str]]):
    for by, value in locators:
        try:
            elements = driver.find_elements(by, value)
        except Exception:
            continue
        for element in elements:
            try:
                if element.is_displayed():
                    return element
            except Exception:
                continue
    return None


def wait_for_authenticated_state(driver: webdriver.Chrome, timeout_seconds: int = 900) -> PortalState:
    deadline = time.time() + timeout_seconds
    last_state = read_state(driver)
    while time.time() < deadline:
        try:
            last_state = read_state(driver)
        except Exception:
            time.sleep(1)
            continue
        if last_state.authenticated:
            return last_state
        time.sleep(2)
    raise TimeoutException(f"No se detectó autenticación en {timeout_seconds} segundos. Última URL: {last_state.url}")


def write_status(path: Path, message: str) -> None:
    path.write_text(message, encoding="utf-8")


def main() -> int:
    run_dir = build_artifact_dir()
    status_path = run_dir / "status.txt"
    summary_path = run_dir / "run-summary.json"
    portal_url = os.getenv("DGII_CERT_PORTAL_URL", DEFAULT_CERT_PORTAL_URL)

    write_status(status_path, "STARTING")
    driver = configure_driver()
    try:
        driver.get(portal_url)
        WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        initial_state = capture(driver, run_dir, "login_page")

        auto_login_attempted = try_fill_login(driver)
        if auto_login_attempted:
            write_status(status_path, "AUTO_LOGIN_ATTEMPTED")
        else:
            write_status(
                status_path,
                "WAITING_FOR_HUMAN_LOGIN: complete login/MFA/CAPTCHA in the visible Chrome window for DGII CERT portal.",
            )

        authenticated_state = wait_for_authenticated_state(driver)
        capture(driver, run_dir, "authenticated_portal")

        summary = {
            "environment": "CERT",
            "portal_url": portal_url,
            "auto_login_attempted": auto_login_attempted,
            "initial_state": asdict(initial_state),
            "authenticated_state": asdict(authenticated_state),
            "artifact_dir": str(run_dir),
            "status_file": str(status_path),
        }
        summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
        write_status(status_path, f"AUTHENTICATED: {authenticated_state.url}")

        print(json.dumps(summary, ensure_ascii=False))
        time.sleep(5)
        return 0
    except Exception as exc:
        failure = {
            "environment": "CERT",
            "portal_url": portal_url,
            "error": str(exc),
            "artifact_dir": str(run_dir),
            "status_file": str(status_path),
        }
        summary_path.write_text(json.dumps(failure, ensure_ascii=False, indent=2), encoding="utf-8")
        write_status(status_path, f"FAILED: {exc}")
        print(json.dumps(failure, ensure_ascii=False))
        return 1
    finally:
        driver.quit()


if __name__ == "__main__":
    raise SystemExit(main())
