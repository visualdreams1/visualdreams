"""Minimal HTTPS-ready WhatsApp webhook receiver.

Run behind a public HTTPS reverse proxy. It accepts Meta verification GETs and
validates POST signatures before appending incoming WhatsApp text messages to
state/inbound_replies.jsonl for the Growth Stack outcome engine.
"""
from __future__ import annotations
import hashlib, hmac, json, os
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT=Path(__file__).resolve().parent
STATE=ROOT/"state"; STATE.mkdir(exist_ok=True)
INBOUND=STATE/"inbound_replies.jsonl"
VERIFY_TOKEN=os.getenv("WHATSAPP_WEBHOOK_VERIFY_TOKEN","")
APP_SECRET=os.getenv("WHATSAPP_APP_SECRET","")


def valid_signature(body: bytes, signature: str) -> bool:
    if not APP_SECRET or not signature.startswith("sha256="):
        return False
    expected="sha256="+hmac.new(APP_SECRET.encode(),body,hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected,signature)


def extract_events(payload: dict) -> list[dict]:
    events=[]
    for entry in payload.get("entry",[]) or []:
        for change in entry.get("changes",[]) or []:
            value=change.get("value",{}) or {}
            for msg in value.get("messages",[]) or []:
                if msg.get("type")!="text":
                    continue
                events.append({
                    "event_id":msg.get("id"),
                    "from":msg.get("from"),
                    "text":((msg.get("text") or {}).get("body") or "").strip(),
                    "at":msg.get("timestamp"),
                    "channel":"whatsapp",
                    "raw_type":msg.get("type"),
                })
    return [e for e in events if e.get("event_id") and e.get("text")]


class Handler(BaseHTTPRequestHandler):
    def send_text(self, code:int, text:str):
        data=text.encode()
        self.send_response(code); self.send_header("Content-Type","text/plain"); self.send_header("Content-Length",str(len(data))); self.end_headers(); self.wfile.write(data)

    def do_GET(self):
        q=parse_qs(urlparse(self.path).query)
        if q.get("hub.mode",[""])[0]=="subscribe" and q.get("hub.verify_token",[""])[0]==VERIFY_TOKEN and VERIFY_TOKEN:
            self.send_text(200,q.get("hub.challenge",[""])[0]); return
        self.send_text(403,"verification failed")

    def do_POST(self):
        length=int(self.headers.get("Content-Length","0")); body=self.rfile.read(length)
        if not valid_signature(body,self.headers.get("X-Hub-Signature-256","")):
            self.send_text(401,"invalid signature"); return
        try: payload=json.loads(body.decode("utf-8"))
        except Exception: self.send_text(400,"invalid json"); return
        with INBOUND.open("a",encoding="utf-8") as f:
            for event in extract_events(payload): f.write(json.dumps(event,ensure_ascii=False)+"\n")
        self.send_text(200,"EVENT_RECEIVED")

    def log_message(self, fmt, *args): return


def main():
    port=int(os.getenv("PORT","8080"))
    if not VERIFY_TOKEN or not APP_SECRET:
        raise SystemExit("Set WHATSAPP_WEBHOOK_VERIFY_TOKEN and WHATSAPP_APP_SECRET")
    HTTPServer(("0.0.0.0",port),Handler).serve_forever()

if __name__=="__main__": main()
