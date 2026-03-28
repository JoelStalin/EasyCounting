from __future__ import annotations

import argparse
import hashlib
import re
from http.cookiejar import CookieJar
from pathlib import Path
from urllib import parse as urlparse
from urllib import request as urlrequest


DEFAULT_BASE_URL = "https://ra.viafirma.do/ra/viafirmard/requestCheck/{request_code}"


def _extract_view_state(html: str) -> str:
    match = re.search(r'name="javax\.faces\.ViewState"[^>]+value="([^"]+)"', html)
    if not match:
        raise RuntimeError("No fue posible localizar javax.faces.ViewState en la pagina de Viafirma")
    return match.group(1)


def _extract_filename(content_disposition: str | None, request_code: str) -> str:
    if not content_disposition:
        return f"{request_code}.p12"
    match = re.search(r'filename="?([^";]+)"?', content_disposition)
    if not match:
        return f"{request_code}.p12"
    return match.group(1)


def redownload_viafirma_certificate(
    request_code: str,
    *,
    output_dir: str | Path,
    base_url_template: str = DEFAULT_BASE_URL,
) -> Path:
    request_code = (request_code or "").strip()
    if not request_code:
        raise RuntimeError("request_code es obligatorio")

    url = base_url_template.format(request_code=request_code)
    destination_dir = Path(output_dir)
    destination_dir.mkdir(parents=True, exist_ok=True)

    cookie_jar = CookieJar()
    opener = urlrequest.build_opener(urlrequest.HTTPCookieProcessor(cookie_jar))

    with opener.open(url, timeout=60) as response:
        html = response.read().decode("utf-8", errors="ignore")

    view_state = _extract_view_state(html)
    form = urlparse.urlencode(
        {
            "formProcessReq": "formProcessReq",
            "formProcessReq:j_idt339": "formProcessReq:j_idt339",
            "codRa": "viafirmard",
            "codRequest": request_code,
            "javax.faces.ViewState": view_state,
        }
    ).encode("utf-8")

    post_request = urlrequest.Request(
        url,
        data=form,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    with opener.open(post_request, timeout=120) as response:
        payload = response.read()
        filename = _extract_filename(response.headers.get("Content-Disposition"), request_code)

    output_path = destination_dir / filename
    output_path.write_bytes(payload)
    return output_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Re-descarga un certificado .p12 desde Viafirma RA")
    parser.add_argument("--request-code", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()

    output_path = redownload_viafirma_certificate(args.request_code, output_dir=args.output_dir)
    digest = hashlib.sha256(output_path.read_bytes()).hexdigest().upper()
    print(f"{output_path}|SHA256={digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
