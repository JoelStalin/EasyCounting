#!/usr/bin/env python3
import json
import os
import subprocess
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


HOST = "0.0.0.0"
PORT = 9000
TOKEN = os.environ["DEPLOY_HOOK_TOKEN"]
SCRIPT = os.environ["DEPLOY_SCRIPT"]


class Handler(BaseHTTPRequestHandler):
    def do_POST(self) -> None:
        if self.path != "/deploy":
            self.send_response(404)
            self.end_headers()
            return

        if self.headers.get("Authorization") != f"Bearer {TOKEN}":
            self.send_response(401)
            self.end_headers()
            return

        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length) if length else b""
        if body:
            try:
                json.loads(body.decode("utf-8"))
            except json.JSONDecodeError:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b"invalid json")
                return

        try:
            completed = subprocess.run(
                [SCRIPT],
                check=True,
                capture_output=True,
                text=True,
                timeout=3600,
            )
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(
                json.dumps({"status": "ok", "stdout": completed.stdout[-4000:]}).encode("utf-8")
            )
        except subprocess.CalledProcessError as exc:
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(
                json.dumps(
                    {
                        "status": "error",
                        "stdout": exc.stdout[-4000:],
                        "stderr": exc.stderr[-4000:],
                    }
                ).encode("utf-8")
            )
        except subprocess.TimeoutExpired:
            self.send_response(504)
            self.end_headers()
            self.wfile.write(b"deploy timeout")

    def log_message(self, fmt: str, *args) -> None:
        return


if __name__ == "__main__":
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
