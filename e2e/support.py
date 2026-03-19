import os
import re
import time
from pathlib import Path

from selenium.common.exceptions import StaleElementReferenceException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

_ARTIFACTS_DIR = Path(os.getenv("ARTIFACTS_DIR", Path(__file__).resolve().parents[1] / "e2e" / "artifacts"))
_STEP_COUNTER = 0
_TOUR_ROOT_SELECTOR = ".react-joyride__tooltip, .react-joyride__overlay, [data-test-id='tooltip'], [data-test-id='overlay']"
_TOUR_DISMISS_SELECTORS = [
    "[data-test-id='button-skip']",
    "[data-action='skip']",
    "[data-test-id='button-close']",
    "[data-action='close']",
    "[data-test-id='button-primary']",
]


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


def ensure_tour_visible(driver, expected_text: str | None = None, timeout: int = 20) -> None:
    try:
        WebDriverWait(driver, 5).until(lambda d: _tour_matches(d, expected_text))
        return
    except TimeoutException:
        trigger = WebDriverWait(driver, timeout).until(EC.presence_of_element_located((By.CSS_SELECTOR, "[data-tour='tour-trigger']")))
        driver.execute_script("arguments[0].click()", trigger)
        WebDriverWait(driver, timeout).until(lambda d: _tour_matches(d, expected_text))
    _slow_mo_pause()


def dismiss_tour(driver, timeout: int = 20) -> None:
    dismiss_button = WebDriverWait(driver, timeout).until(lambda d: _find_visible_tour_button(d))
    driver.execute_script("arguments[0].click()", dismiss_button)
    WebDriverWait(driver, timeout).until(lambda d: not _find_visible_tour_root(d))
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


def _find_visible_tour_root(driver):
    for selector in _TOUR_ROOT_SELECTOR.split(", "):
        for element in driver.find_elements(By.CSS_SELECTOR, selector):
            try:
                element.get_attribute("class")
                return element
            except StaleElementReferenceException:
                continue
    return None


def _tour_matches(driver, expected_text: str | None) -> bool:
    root = _find_visible_tour_root(driver)
    if root is None:
        return False
    if not expected_text:
        return True
    candidate_text = " ".join(
        filter(
            None,
            [
                root.text,
                root.get_attribute("innerText"),
                root.get_attribute("textContent"),
                root.get_attribute("aria-label"),
                root.get_attribute("title"),
            ],
        )
    )
    return expected_text in candidate_text or _find_visible_tour_button(driver) is not None


def _find_visible_tour_button(driver):
    for selector in _TOUR_DISMISS_SELECTORS:
        for element in driver.find_elements(By.CSS_SELECTOR, selector):
            try:
                element.get_attribute("data-test-id")
                return element
            except StaleElementReferenceException:
                continue
    return None
