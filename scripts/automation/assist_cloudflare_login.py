from __future__ import annotations

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
    
    IMPORTANTE: NO hardcodear credenciales en este archivo.
    
    Credenciales deben venir de:
    1. Variables de entorno: CLOUDFLARE_EMAIL, CLOUDFLARE_PASSWORD
    2. O mejor: CLOUDFLARE_API_TOKEN (en lugar de user/pass)
    3. Gestor de credenciales del SO (Windows Credential Manager)
    
    RIESGOS SI USAS USER/PASS:
    - Quedan expuestas en control de versiones
    - Quedan en histórico de git
    - No se pueden rotar fácilmente
    
    RECOMENDACIÓN:
    - Usar API Token de Cloudflare
    - Guardar en gestor seguro de credenciales
    - No versionar en repositorio
    """
    
    # Obtener credenciales de variables de entorno (NUNCA hardcodear)
    cf_email = os.getenv("CLOUDFLARE_EMAIL")
    cf_password = os.getenv("CLOUDFLARE_PASSWORD")
    
    if not cf_email or not cf_password:
        print("ERROR: Credenciales de Cloudflare no configuradas.")
        print("\nConfigura variables de entorno:")
        print("  Windows:")
        print("    $env:CLOUDFLARE_EMAIL='tu-email@example.com'")
        print("    $env:CLOUDFLARE_PASSWORD='tu-contraseña-segura'")
        print("\n  O mejor aún, usa Cloudflare API Token:")
        print("    $env:CLOUDFLARE_API_TOKEN='tu-api-token'")
        print("\nObtén el API Token en:")
        print("  https://dash.cloudflare.com/profile/api-tokens")
        return 1
    
    out_dir = Path("artifacts_live_dns")
    out_dir.mkdir(exist_ok=True)
    status_path = out_dir / "cloudflare_assisted_status.txt"
    write_status(status_path, "STARTING")

    opts = webdriver.ChromeOptions()
    opts.add_argument("--window-size=1440,1100")
    opts.add_experimental_option("excludeSwitches", ["enable-automation"])
    opts.add_experimental_option("useAutomationExtension", False)

    driver = webdriver.Chrome(options=opts)
    wait = WebDriverWait(driver, 40)

    try:
        target = "https://dash.cloudflare.com/"
        driver.get(target)

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
        (out_dir / "cloudflare_assisted_ready.html").write_text(
            driver.page_source, encoding="utf-8"
        )
        write_status(
            status_path,
            "WAITING_FOR_HUMAN: complete Cloudflare verification in the visible browser window.",
        )

        deadline = time.time() + 1800
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
                    driver.save_screenshot(
                        str(out_dir / "cloudflare_assisted_entered_dashboard.png")
                    )
                    (out_dir / "cloudflare_assisted_entered_dashboard.html").write_text(
                        driver.page_source, encoding="utf-8"
                    )
                    write_status(status_path, f"ENTERED_DASHBOARD: {current_url}")
                    time.sleep(5)
                    return 0
            time.sleep(2)

        driver.save_screenshot(str(out_dir / "cloudflare_assisted_timeout.png"))
        (out_dir / "cloudflare_assisted_timeout.html").write_text(
            driver.page_source, encoding="utf-8"
        )
        write_status(status_path, f"TIMEOUT: {driver.current_url}")
        return 1
    finally:
        driver.quit()


if __name__ == "__main__":
    sys.exit(main())
