from __future__ import annotations

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
            email.send_keys("Joelstalin2105@gmail.com")
            password = driver.find_element(By.NAME, "password")
            password.clear()
            password.send_keys("Pandemia@2020#covid")

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
