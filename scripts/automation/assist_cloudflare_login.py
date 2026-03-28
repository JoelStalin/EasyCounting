from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


def write_status(path: Path, message: str) -> None:
    path.write_text(message, encoding="utf-8")


def main() -> int:
    """
    Asistente seguro para login en Cloudflare.

    Permite abrir Chrome con perfil real para reutilizar sesion ya iniciada.
    No requiere credenciales si la sesion ya existe en el perfil.
    """

    parser = argparse.ArgumentParser(description="Asistente Selenium para Cloudflare Dashboard")
    parser.add_argument(
        "--start-url",
        default="https://dash.cloudflare.com/",
        help="URL inicial del dashboard",
    )
    parser.add_argument(
        "--user-data-dir",
        default=None,
        help="Directorio User Data de Chrome",
    )
    parser.add_argument(
        "--profile-directory",
        default=None,
        help="Nombre de perfil de Chrome (ej: Default, Profile 1)",
    )
    parser.add_argument(
        "--timeout-seconds",
        type=int,
        default=1800,
        help="Tiempo maximo de espera para detectar dashboard",
    )
    args = parser.parse_args()

    # Credenciales opcionales via env (NO hardcodear)
    cf_email = os.getenv("CLOUDFLARE_EMAIL")
    cf_password = os.getenv("CLOUDFLARE_PASSWORD")

    out_dir = Path("artifacts_live_dns")
    out_dir.mkdir(exist_ok=True)
    status_path = out_dir / "cloudflare_assisted_status.txt"
    write_status(status_path, "STARTING")

    opts = webdriver.ChromeOptions()
    opts.add_argument("--window-size=1440,1100")
    opts.add_experimental_option("excludeSwitches", ["enable-automation"])
    opts.add_experimental_option("useAutomationExtension", False)
    if args.user_data_dir:
        opts.add_argument(f"--user-data-dir={args.user_data_dir}")
    if args.profile_directory:
        opts.add_argument(f"--profile-directory={args.profile_directory}")

    driver = webdriver.Chrome(options=opts)
    wait = WebDriverWait(driver, 40)

    try:
        driver.get(args.start_url)

        # Intento de login solo si hay credenciales cargadas
        if cf_email and cf_password:
            try:
                email = wait.until(EC.presence_of_element_located((By.NAME, "email")))
                email.clear()
                email.send_keys(cf_email)
                password = driver.find_element(By.NAME, "password")
                password.clear()
                password.send_keys(cf_password)

                for selector in (
                    "button[type='submit']",
                    "button[data-testid='login-submit-btn']",
                ):
                    try:
                        driver.find_element(By.CSS_SELECTOR, selector).click()
                        break
                    except Exception:
                        continue
            except Exception:
                pass

        driver.save_screenshot(str(out_dir / "cloudflare_assisted_ready.png"))
        (out_dir / "cloudflare_assisted_ready.html").write_text(driver.page_source, encoding="utf-8")
        write_status(
            status_path,
            "WAITING_FOR_HUMAN: complete Cloudflare verification in the visible browser window.",
        )

        deadline = time.time() + max(60, int(args.timeout_seconds))
        while time.time() < deadline:
            current_url = driver.current_url
            current_url_lower = current_url.lower()
            if (
                "dash.cloudflare.com/login" not in current_url_lower
                and "challenge" not in current_url_lower
                and "turnstile" not in current_url_lower
            ):
                page = driver.page_source.lower()
                if (
                    "dash.cloudflare.com" in current_url_lower
                    and (
                        "/home" in current_url_lower
                        or "websites" in page
                        or "account home" in page
                        or "overview" in page
                    )
                ):
                    driver.save_screenshot(str(out_dir / "cloudflare_assisted_entered_dashboard.png"))
                    (out_dir / "cloudflare_assisted_entered_dashboard.html").write_text(
                        driver.page_source, encoding="utf-8"
                    )
                    write_status(status_path, f"ENTERED_DASHBOARD: {current_url}")
                    time.sleep(5)
                    return 0
            time.sleep(2)

        driver.save_screenshot(str(out_dir / "cloudflare_assisted_timeout.png"))
        (out_dir / "cloudflare_assisted_timeout.html").write_text(driver.page_source, encoding="utf-8")
        write_status(status_path, f"TIMEOUT: {driver.current_url}")
        return 1
    finally:
        driver.quit()


if __name__ == "__main__":
    sys.exit(main())
