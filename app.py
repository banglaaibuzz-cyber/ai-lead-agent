#!/usr/bin/env python3
"""Tiny zero-dependency web UI for the AI Lead Agent."""
from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from src.lead_agent import research_target

ROOT = Path(__file__).resolve().parent
INDEX = ROOT / "web" / "index.html"


class Handler(BaseHTTPRequestHandler):
    def _send(self, status: int, content_type: str, body: bytes) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path == "/":
            self._send(200, "text/html; charset=utf-8", INDEX.read_bytes())
            return
        if parsed.path == "/health":
            self._send(200, "application/json", b'{"ok":true}')
            return
        self._send(404, "text/plain; charset=utf-8", b"Not found")

    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/api/research":
            self._send(404, "application/json", b'{"error":"Not found"}')
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length) or b"{}")
            target = str(payload.get("target", "")).strip()
            results = int(payload.get("results", 5))
            if not target:
                raise ValueError("Enter an industry, niche, location, or company type.")
            results = max(1, min(results, 8))
            leads = research_target(target, max_results=results, delay=0.6)
            body = json.dumps([lead.__dict__ for lead in leads], ensure_ascii=False).encode()
            self._send(200, "application/json; charset=utf-8", body)
        except Exception as exc:
            body = json.dumps({"error": str(exc)}).encode()
            self._send(400, "application/json; charset=utf-8", body)

    def log_message(self, fmt: str, *args: object) -> None:
        print(fmt % args)


if __name__ == "__main__":
    server = ThreadingHTTPServer(("127.0.0.1", 8000), Handler)
    print("AI Lead Agent UI: http://127.0.0.1:8000")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
