#!/usr/bin/env python3
"""Zero-dependency web UI for the AI Lead Agent."""
from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from src.lead_agent import research_target
from src.quality import assess

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
            category = str(payload.get("category", "HVAC companies")).strip()
            market = str(payload.get("market", "United States")).strip()
            location = str(payload.get("location", "")).strip()
            goal = str(payload.get("goal", "find businesses with operational problems and automation opportunities")).strip()
            results = max(1, min(int(payload.get("results", 6)), 8))
            if not category or not market:
                raise ValueError("Category and market are required.")
            target = f"{category} in {location + ', ' if location else ''}{market}. Goal: {goal}"
            leads = research_target(target, max_results=results, delay=0.6)
            response = []
            for lead in leads:
                item = dict(lead.__dict__)
                quality = assess(
                    score=lead.score,
                    evidence=lead.evidence,
                    opportunities=lead.opportunities,
                    url=lead.url,
                )
                item["priority"] = quality.priority
                item["confidence"] = quality.confidence
                item["tier"] = quality.tier
                item["next_action"] = quality.next_action
                response.append(item)
            response.sort(key=lambda x: (x["priority"], x["score"]), reverse=True)
            body = json.dumps(response, ensure_ascii=False).encode()
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
