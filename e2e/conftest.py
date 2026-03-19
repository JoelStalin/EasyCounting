import os
import socket
import time
from contextlib import suppress
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from urllib.error import URLError
from urllib.parse import unquote, urlparse
from urllib.request import urlopen

import pytest
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.edge.options import Options as EdgeOptions

from e2e.mock_api import start_mock_api_server
from e2e.support import finalize_demo_run, start_demo_run

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = Path(os.getenv("ARTIFACTS_DIR", ROOT / "e2e" / "artifacts"))
ARTIFACTS.mkdir(parents=True, exist_ok=True)


def _find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        sock.listen(1)
        return int(sock.getsockname()[1])


def _wait_for_http(url: str, *, timeout: float = 60.0) -> None:
    deadline = time.time() + timeout
    last_error: str | None = None
    while time.time() < deadline:
        try:
            with urlopen(url, timeout=2) as response:  # noqa: S310
                if 200 <= response.status < 500:
                    return
        except URLError as exc:
            last_error = str(exc)
        time.sleep(0.5)
    raise RuntimeError(f"No fue posible alcanzar {url}. Ultimo error: {last_error or 'sin respuesta'}")


def _spa_handler_for(directory: Path):
    root = directory.resolve()

    class SpaHandler(SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(root), **kwargs)

        def log_message(self, format: str, *args) -> None:  # noqa: A003
            return

        def do_GET(self) -> None:  # noqa: N802
            parsed = urlparse(self.path)
            requested = (root / unquote(parsed.path.lstrip("/"))).resolve()
            if parsed.path not in {"", "/"}:
                try:
                    requested.relative_to(root)
                except ValueError:
                    self.send_error(403)
                    return
            if parsed.path in {"", "/"} or requested.exists():
                super().do_GET()
                return
            self.path = "/index.html"
            super().do_GET()

    return SpaHandler


def _start_static_portal_server(directory: Path, port: int) -> tuple[ThreadingHTTPServer, Thread]:
    if not directory.exists():
        raise RuntimeError(f"No existe el directorio de portal compilado: {directory}")
    server = ThreadingHTTPServer(("127.0.0.1", port), _spa_handler_for(directory))
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    _wait_for_http(f"http://127.0.0.1:{port}/login", timeout=20.0)
    return server, thread


@pytest.fixture(scope="session")
def api_base_url() -> str:
    return os.getenv("API_BASE_URL", "http://localhost:8000")


@pytest.fixture(scope="session")
def mock_api_server(api_base_url: str) -> str:
    if os.getenv("ADMIN_BASE_URL") and os.getenv("CLIENT_BASE_URL"):
        yield api_base_url
        return
    server, thread = start_mock_api_server(api_base_url)
    _wait_for_http(f"{api_base_url}/__health__", timeout=20.0)
    yield api_base_url
    server.shutdown()
    thread.join(timeout=5)


@pytest.fixture(scope="session")
def frontend_servers(mock_api_server: str) -> dict[str, str]:
    external_admin = os.getenv("ADMIN_BASE_URL")
    external_client = os.getenv("CLIENT_BASE_URL")
    external_seller = os.getenv("SELLER_BASE_URL")
    if external_admin and external_client and external_seller:
        yield {
            "admin": external_admin.rstrip("/"),
            "client": external_client.rstrip("/"),
            "seller": external_seller.rstrip("/"),
            "api": mock_api_server,
        }
        return

    admin_port = _find_free_port()
    client_port = _find_free_port()
    seller_port = _find_free_port()
    admin_server, admin_thread = _start_static_portal_server(
        ROOT / "frontend" / "apps" / "admin-portal" / "dist",
        admin_port,
    )
    client_server, client_thread = _start_static_portal_server(
        ROOT / "frontend" / "apps" / "client-portal" / "dist",
        client_port,
    )
    seller_server, seller_thread = _start_static_portal_server(
        ROOT / "frontend" / "apps" / "seller-portal" / "dist",
        seller_port,
    )
    urls = {
        "admin": f"http://127.0.0.1:{admin_port}",
        "client": f"http://127.0.0.1:{client_port}",
        "seller": f"http://127.0.0.1:{seller_port}",
        "api": mock_api_server,
    }
    yield urls
    with suppress(Exception):
        seller_server.shutdown()
    with suppress(Exception):
        client_server.shutdown()
    with suppress(Exception):
        admin_server.shutdown()
    seller_thread.join(timeout=5)
    client_thread.join(timeout=5)
    admin_thread.join(timeout=5)


@pytest.fixture(scope="session")
def admin_url(frontend_servers: dict[str, str]) -> str:
    return frontend_servers["admin"]


@pytest.fixture(scope="session")
def client_url(frontend_servers: dict[str, str]) -> str:
    return frontend_servers["client"]


@pytest.fixture(scope="session")
def seller_url(frontend_servers: dict[str, str]) -> str:
    return frontend_servers["seller"]


def _installed_browser_binary(browser_name: str) -> str | None:
    candidates = {
        "chrome": [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        ],
        "edge": [
            r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        ],
    }
    for candidate in candidates.get(browser_name, []):
        if Path(candidate).exists():
            return candidate
    return None


def _build_driver() -> webdriver.Remote:
    errors: list[str] = []
    preferred_browser = os.getenv("BROWSER", "chrome").strip().lower()
    headless = os.getenv("HEADLESS", "1") == "1"

    chrome_options = ChromeOptions()
    chrome_options.add_argument("--window-size=1440,960")
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-features=HttpsOnlyMode,HttpsFirstBalancedModeAutoEnable,HttpsUpgrades")
    chrome_binary = _installed_browser_binary("chrome")
    if chrome_binary:
        chrome_options.binary_location = chrome_binary
    if headless:
        chrome_options.add_argument("--headless=new")

    edge_options = EdgeOptions()
    edge_options.add_argument("--window-size=1440,960")
    edge_options.add_argument("--start-maximized")
    edge_options.add_argument("--disable-gpu")
    edge_options.add_argument("--disable-features=HttpsOnlyMode,HttpsFirstBalancedModeAutoEnable,HttpsUpgrades")
    edge_binary = _installed_browser_binary("edge")
    if edge_binary:
        edge_options.binary_location = edge_binary
    if headless:
        edge_options.add_argument("--headless=new")

    browser_candidates = (
        ("chrome", webdriver.Chrome, chrome_options),
        ("edge", webdriver.Edge, edge_options),
    )
    ordered_candidates = sorted(
        browser_candidates,
        key=lambda item: item[0] != preferred_browser,
    )

    for browser_name, factory, options in ordered_candidates:
        try:
            driver = factory(options=options)
            driver.set_page_load_timeout(30)
            driver.implicitly_wait(0)
            return driver
        except WebDriverException as exc:
            errors.append(f"{browser_name}: {exc.msg}")
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{browser_name}: {exc}")

    raise RuntimeError("No fue posible iniciar un navegador Selenium. " + " | ".join(errors))


@pytest.fixture
def driver(frontend_servers: dict[str, str]):
    start_demo_run(ARTIFACTS)
    drv = _build_driver()
    yield drv
    finalize_demo_run(drv)
    drv.quit()


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep = outcome.get_result()
    if rep.when == "call" and rep.failed:
        drv = item.funcargs.get("driver")
        if drv:
            safe_name = item.nodeid.replace("::", "__").replace("/", "_").replace("\\", "_")
            path = ARTIFACTS / f"{safe_name}.png"
            drv.save_screenshot(str(path))
