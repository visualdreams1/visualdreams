"""Production-ready Meta WhatsApp webhook receiver plus NEXUS dashboard."""
from __future__ import annotations

import hashlib
import hmac
import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from nexus_dashboard import html_page, summary

ROOT = Path(__file__).resolve().parent
STATE = ROOT / "state"
STATE.mkdir(exist_ok=True)
INBOUND = STATE / "inbound_replies.jsonl"


def valid_signature(body: bytes, signature: str) -> bool:
    app_secret = os.getenv("WHATSAPP_APP_SECRET", "")
    if not app_secret or not signature.startswith("sha256="):
        return False
    expected = "sha256=" + hmac.new(app_secret.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


def extract_events(payload: dict) -> list[dict]:
    events = []
    for entry in payload.get("entry", []) or []:
        for change in entry.get("changes", []) or []:
            value = change.get("value", {}) or {}
            for msg in value.get("messages", []) or []:
                if msg.get("type") != "text":
                    continue
                events.append({
                    "event_id": msg.get("id"), "from": msg.get("from"),
                    "text": ((msg.get("text") or {}).get("body") or "").strip(),
                    "at": msg.get("timestamp"), "channel": "whatsapp", "raw_type": msg.get("type"),
                })
    return [e for e in events if e.get("event_id") and e.get("text")]


class Handler(BaseHTTPRequestHandler):
    def send_text(self, code: int, text: str, content_type: str = "text/plain; charset=utf-8"):
        data = text.encode()
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/health":
            configured = bool(os.getenv("WHATSAPP_WEBHOOK_VERIFY_TOKEN")) and bool(os.getenv("WHATSAPP_APP_SECRET"))
            self.send_text(200, json.dumps({"status": "ok", "whatsapp_webhook_configured": configured}), "application/json")
            return
        if parsed.path == "/api/nexus":
            self.send_text(200, json.dumps(summary(), ensure_ascii=False), "application/json")
            return
        if parsed.path in {"/nexus", "/dashboard"}:
            self.send_text(200, html_page(summary()), "text/html; charset=utf-8")
            return

        q = parse_qs(parsed.query)
        verify_token = os.getenv("WHATSAPP_WEBHOOK_VERIFY_TOKEN", "")
        if (parsed.path in {"/", "/webhook"} and q.get("hub.mode", [""])[0] == "subscribe"
                and q.get("hub.verify_token", [""])[0] == verify_token and verify_token):
            self.send_text(200, q.get("hub.challenge", [""])[0])
            return
        self.send_text(403, "verification failed")

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path not in {"/", "/webhook"}:
            self.send_text(404, "not found")
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            self.send_text(400, "invalid content length")
            return
        body = self.rfile.read(length)
        if not valid_signature(body, self.headers.get("X-Hub-Signature-256", "")):
            self.send_text(401, "invalid signature")
            return
        try:
            payload = json.loads(body.decode("utf-8"))
        except Exception:
            self.send_text(400, "invalid json")
            return
        existing = set()
        if INBOUND.exists():
            for line in INBOUND.read_text(encoding="utf-8").splitlines()[-5000:]:
                try:
                    event = json.loads(line)
                    if event.get("event_id"):
                        existing.add(event["event_id"])
                except Exception:
                    pass
        with INBOUND.open("a", encoding="utf-8") as f:
            for event in extract_events(payload):
                if event["event_id"] in existing:
                    continue
                f.write(json.dumps(event, ensure_ascii=False) + "\n")
                existing.add(event["event_id"])
        self.send_text(200, "EVENT_RECEIVED")

    def log_message(self, fmt, *args):
        return


def main():
    port = int(os.getenv("PORT", "10000"))
    HTTPServer(("0.0.0.0", port), Handler).serve_forever()


if __name__ == "__main__":
    main()
