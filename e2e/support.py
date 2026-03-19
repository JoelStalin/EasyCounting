import os
import re
import time
from pathlib import Path

from selenium.webdriver.support.ui import WebDriverWait

_ARTIFACTS_DIR = Path(os.getenv("ARTIFACTS_DIR", Path(__file__).resolve().parents[1] / "e2e" / "artifacts"))
_STEP_COUNTER = 0


def start_demo_run(artifacts_dir: Path) -> None:
    global _ARTIFACTS_DIR, _STEP_COUNTER
    _ARTIFACTS_DIR = Path(artifacts_dir)
    _ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    _STEP_COUNTER = 0


def wait_for_ready(driver, timeout: int = 20):
    WebDriverWait(driver, timeout).until(lambda d: d.execute_script("return document.readyState") == "complete")
    _slow_mo_pause()


def record_step(driver, name: str) -> None:
    global _STEP_COUNTER
    _STEP_COUNTER += 1
    slug = _slugify(name)
    screenshot_path = _ARTIFACTS_DIR / f"{_STEP_COUNTER:02d}_{slug}.png"
    driver.save_screenshot(str(screenshot_path))
    _slow_mo_pause()


def finalize_demo_run(driver) -> None:
    keep_open_ms = int(os.getenv("KEEP_OPEN_MS", "0") or "0")
    if keep_open_ms > 0:
        time.sleep(keep_open_ms / 1000)
    record_step(driver, "suite_complete")


def _slow_mo_pause() -> None:
    delay_ms = int(os.getenv("SLOW_MO_MS", "0") or "0")
    if delay_ms > 0:
        time.sleep(delay_ms / 1000)


def _slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.strip().lower()).strip("_") or "step"
