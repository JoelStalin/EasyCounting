from __future__ import annotations

import argparse
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import unquote, urlparse
from urllib.request import Request, urlopen


def _emit_runtime_config(handler: SimpleHTTPRequestHandler, runtime_api_base_url: str | None) -> None:
    body = f"window.__GETUPSOFT_API_BASE_URL__ = {runtime_api_base_url!r};\n".encode("utf-8")
    handler.send_response(200)
    handler.send_header("Content-Type", "application/javascript; charset=utf-8")
    handler.send_header("Cache-Control", "no-store")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


_HOP_BY_HOP_HEADERS = {
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailers",
    "transfer-encoding",
    "upgrade",
}

_PROXY_PREFIXES = (
    "/api",
    "/ri",
    "/receptor",
    "/health",
    "/healthz",
    "/livez",
    "/readyz",
    "/metrics",
)


def _should_proxy(path: str) -> bool:
    for prefix in _PROXY_PREFIXES:
        if path == prefix or path.startswith(prefix + "/"):
            return True
    return False


def _proxy_request(handler: SimpleHTTPRequestHandler, upstream_base_url: str) -> None:
    parsed = urlparse(handler.path)
    upstream_url = upstream_base_url.rstrip("/") + parsed.path
    if parsed.query:
        upstream_url += f"?{parsed.query}"

    content_length = int(handler.headers.get("Content-Length", "0") or "0")
    body = handler.rfile.read(content_length) if content_length > 0 else None

    headers = {}
    for key, value in handler.headers.items():
        if key.lower() in _HOP_BY_HOP_HEADERS:
            continue
        if key.lower() == "host":
            continue
        headers[key] = value

    try:
        request = Request(upstream_url, data=body, headers=headers, method=handler.command)
        with urlopen(request, timeout=60) as response:  # noqa: S310
            response_body = response.read()
            handler.send_response(response.getcode())
            for key, value in response.headers.items():
                lower_key = key.lower()
                if lower_key in _HOP_BY_HOP_HEADERS or lower_key == "content-length":
                    continue
                handler.send_header(key, value)
            handler.send_header("Content-Length", str(len(response_body)))
            handler.end_headers()
            if handler.command != "HEAD":
                handler.wfile.write(response_body)
    except HTTPError as exc:
        response_body = exc.read()
        handler.send_response(exc.code)
        for key, value in exc.headers.items():
            lower_key = key.lower()
            if lower_key in _HOP_BY_HOP_HEADERS or lower_key == "content-length":
                continue
            handler.send_header(key, value)
        handler.send_header("Content-Length", str(len(response_body)))
        handler.end_headers()
        if handler.command != "HEAD":
            handler.wfile.write(response_body)
    except URLError as exc:
        handler.send_error(502, f"Upstream unavailable: {exc}")


def _spa_handler_for(directory: Path, runtime_api_base_url: str | None, proxy_api_base_url: str | None):
    root = directory.resolve()

    class SpaHandler(SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(root), **kwargs)

        def log_message(self, format: str, *args) -> None:  # noqa: A003
            return

        def do_GET(self) -> None:  # noqa: N802
            parsed = urlparse(self.path)
            if proxy_api_base_url and _should_proxy(parsed.path):
                _proxy_request(self, proxy_api_base_url)
                return
            if parsed.path == "/runtime-config.js":
                _emit_runtime_config(self, runtime_api_base_url)
                return

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

        def do_HEAD(self) -> None:  # noqa: N802
            parsed = urlparse(self.path)
            if proxy_api_base_url and _should_proxy(parsed.path):
                _proxy_request(self, proxy_api_base_url)
                return
            super().do_HEAD()

        def do_OPTIONS(self) -> None:  # noqa: N802
            if proxy_api_base_url and _should_proxy(urlparse(self.path).path):
                _proxy_request(self, proxy_api_base_url)
                return
            self.send_response(204)
            self.end_headers()

        def do_POST(self) -> None:  # noqa: N802
            if proxy_api_base_url and _should_proxy(urlparse(self.path).path):
                _proxy_request(self, proxy_api_base_url)
                return
            self.send_error(405)

        def do_PUT(self) -> None:  # noqa: N802
            if proxy_api_base_url and _should_proxy(urlparse(self.path).path):
                _proxy_request(self, proxy_api_base_url)
                return
            self.send_error(405)

        def do_PATCH(self) -> None:  # noqa: N802
            if proxy_api_base_url and _should_proxy(urlparse(self.path).path):
                _proxy_request(self, proxy_api_base_url)
                return
            self.send_error(405)

        def do_DELETE(self) -> None:  # noqa: N802
            if proxy_api_base_url and _should_proxy(urlparse(self.path).path):
                _proxy_request(self, proxy_api_base_url)
                return
            self.send_error(405)

    return SpaHandler


def _redirect_handler_for(target: str):
    class RedirectHandler(SimpleHTTPRequestHandler):
        def log_message(self, format: str, *args) -> None:  # noqa: A003
            return

        def _redirect(self) -> None:
            parsed = urlparse(self.path)
            destination = target.rstrip("/") + (parsed.path or "/")
            if parsed.query:
                destination += f"?{parsed.query}"
            self.send_response(301)
            self.send_header("Location", destination)
            self.end_headers()

        def do_GET(self) -> None:  # noqa: N802
            self._redirect()

        def do_HEAD(self) -> None:  # noqa: N802
            self._redirect()

    return RedirectHandler


def main() -> int:
    parser = argparse.ArgumentParser(description="Serve a SPA dist directory with history API fallback.")
    parser.add_argument("--dir", dest="directory", help="Directory containing index.html and assets/")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, required=True)
    parser.add_argument("--runtime-api-base-url", default=None)
    parser.add_argument("--proxy-api-base-url", default=None)
    parser.add_argument("--redirect-target", default=None)
    args = parser.parse_args()

    if args.redirect_target:
        server = ThreadingHTTPServer((args.host, args.port), _redirect_handler_for(args.redirect_target))
        print(f"Redirecting http://{args.host}:{args.port} -> {args.redirect_target}", flush=True)
    else:
        if not args.directory:
            raise SystemExit("--dir is required when --redirect-target is not used")
        directory = Path(args.directory)
        if not directory.exists():
            raise SystemExit(f"Directory does not exist: {directory}")

        server = ThreadingHTTPServer(
            (args.host, args.port),
            _spa_handler_for(directory, args.runtime_api_base_url, args.proxy_api_base_url),
        )
        print(f"Serving {directory} on http://{args.host}:{args.port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.shutdown()
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
