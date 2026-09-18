"""Production-ready Meta WhatsApp webhook receiver plus NEXUS dashboard."""
from __future__ import annotations

import hashlib
import hmac
import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlparse
from urllib.request import Request, urlopen

from nexus_dashboard import html_page, summary
from growth_core import add_lead, create_order, executive_status, products, quote, record_payment
from mpesa_daraja import configured as mpesa_configured, stk_push
from whatsapp_cloud import configured as whatsapp_configured, send_text
from agent_chat import chat as agent_chat

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


def cloudflare_status() -> dict:
    """Validate the Render-injected Cloudflare token without ever returning it."""
    token = os.getenv("CLOUDFLARE_API_TOKEN", "")
    if not token:
        return {"configured": False, "valid": False, "message": "CLOUDFLARE_API_TOKEN is not set"}
    try:
        req = Request(
            "https://api.cloudflare.com/client/v4/user/tokens/verify",
            headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
            method="GET",
        )
        with urlopen(req, timeout=10) as response:
            payload = json.loads(response.read().decode("utf-8"))
        result = payload.get("result") or {}
        return {
            "configured": True,
            "valid": bool(payload.get("success")),
            "status": result.get("status"),
            "message": "Cloudflare token verified" if payload.get("success") else "Cloudflare rejected the token",
        }
    except HTTPError as exc:
        return {"configured": True, "valid": False, "message": f"Cloudflare HTTP {exc.code}"}
    except URLError:
        return {"configured": True, "valid": False, "message": "Could not reach Cloudflare"}
    except Exception:
        return {"configured": True, "valid": False, "message": "Cloudflare verification failed"}


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
        q = parse_qs(parsed.query)
        if parsed.path == "/health":
            configured = bool(os.getenv("WHATSAPP_WEBHOOK_VERIFY_TOKEN")) and bool(os.getenv("WHATSAPP_APP_SECRET"))
            self.send_text(200, json.dumps({
                "status": "ok",
                "whatsapp_webhook_configured": configured,
                "cloudflare_token_configured": bool(os.getenv("CLOUDFLARE_API_TOKEN")),
            }), "application/json")
            return
        if parsed.path == "/agent":
            page = """<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"><title>Growth Stack Agent OS</title><style>body{font-family:system-ui;max-width:760px;margin:auto;padding:16px;background:#f5f5f5}#log{white-space:pre-wrap;background:white;border-radius:12px;padding:16px;min-height:55vh;overflow:auto}textarea{width:100%;box-sizing:border-box;margin-top:10px;padding:12px;border-radius:10px;border:1px solid #ccc}button{margin-top:8px;padding:12px 20px;border:0;border-radius:10px;font-weight:700}</style></head><body><h2>Growth Stack Agent OS</h2><div id="log">Agent OS online. Ask me about the company, customers, offers, system status or next actions.\\n</div><textarea id="m" rows="3" placeholder="Talk to Growth Stack..."></textarea><button onclick="send()">Send</button><script>let h=[];async function send(){let m=document.getElementById('m').value.trim();if(!m)return;let l=document.getElementById('log');l.textContent+='\\nYOU: '+m+'\\n';document.getElementById('m').value='';let r=await fetch('/api/agent/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message:m,history:h})});let j=await r.json();l.textContent+='AGENT: '+(j.reply||j.error||'No response')+'\\n';h.push({role:'user',content:m},{role:'assistant',content:j.reply||''});}</script></body></html>""";
            self.send_text(200, page, "text/html; charset=utf-8")
            return
        if parsed.path == "/api/agent/status":
            self.send_text(200, json.dumps({"online":True,"autonomy":"exception_only","llm_configured":bool(os.getenv("OPENAI_API_KEY")),"model":os.getenv("GROWTH_AGENT_MODEL",os.getenv("OPENAI_MODEL","gpt-5.6"))}), "application/json")
            return
        if parsed.path == "/api/autonomy":
            self.send_text(200, json.dumps({
                "mode": "AUTONOMOUS_WHEN_PROVIDERS_ARE_CONFIGURED",
                "whatsapp": {"configured": whatsapp_configured(), "outbound_enabled": os.getenv("OUTBOUND_ENABLED","false").lower() == "true"},
                "mpesa": {"configured": mpesa_configured()},
                "human_escalation": ["refunds","security","sensitive_requests","provider_failures"]
            }), "application/json")
            return
        if parsed.path == "/cloudflare/status":
            self.send_text(200, json.dumps(cloudflare_status()), "application/json")
            return
        if parsed.path == "/api/nexus":
            data = summary()
            data["commercial"] = executive_status()
            self.send_text(200, json.dumps(data, ensure_ascii=False), "application/json")
            return
        if parsed.path == "/api/status":
            self.send_text(200, json.dumps(executive_status(), ensure_ascii=False), "application/json")
            return
        if parsed.path == "/api/products":
            self.send_text(200, json.dumps({"products": products()}, ensure_ascii=False), "application/json")
            return
        if parsed.path == "/api/quote":
            product_id = q.get("product_id", [""])[0]
            market = q.get("market", ["KE"])[0]
            try:
                self.send_text(200, json.dumps(quote(product_id, market), ensure_ascii=False), "application/json")
            except ValueError as exc:
                self.send_text(400, json.dumps({"error": str(exc)}), "application/json")
            return
        if parsed.path in {"/nexus", "/dashboard"}:
            self.send_text(200, html_page(summary()), "text/html; charset=utf-8")
            return

        verify_token = os.getenv("WHATSAPP_WEBHOOK_VERIFY_TOKEN", "")
        if (parsed.path in {"/", "/webhook"} and q.get("hub.mode", [""])[0] == "subscribe"
                and q.get("hub.verify_token", [""])[0] == verify_token and verify_token):
            self.send_text(200, q.get("hub.challenge", [""])[0])
            return
        self.send_text(403, "verification failed")

    def do_POST(self):
        parsed = urlparse(self.path)
        admin_paths = {"/api/leads", "/api/orders", "/api/payments"}
        if parsed.path in admin_paths:
            expected = os.getenv("GROWTH_ADMIN_API_KEY", "")
            supplied = self.headers.get("X-Growth-Admin-Key", "")
            if not expected or not supplied or not hmac.compare_digest(expected, supplied):
                self.send_text(401, "unauthorized")
                return
            try:
                length = int(self.headers.get("Content-Length", "0"))
                payload = json.loads(self.rfile.read(length).decode("utf-8"))
                if parsed.path == "/api/leads":
                    result = add_lead(payload)
                elif parsed.path == "/api/orders":
                    result = create_order(payload)
                else:
                    result = record_payment(payload.get("order_id", ""), payload.get("status", "PAID"))
                self.send_text(200, json.dumps(result, ensure_ascii=False), "application/json")
            except ValueError as exc:
                self.send_text(400, json.dumps({"error": str(exc)}), "application/json")
            except Exception:
                self.send_text(500, json.dumps({"error": "request failed"}), "application/json")
            return
        if parsed.path == "/mpesa/callback":
            try:
                length = int(self.headers.get("Content-Length", "0"))
                payload = json.loads(self.rfile.read(length).decode("utf-8"))
                callback = payload.get("Body", {}).get("stkCallback", {})
                metadata = {x.get("Name"): x.get("Value") for x in callback.get("CallbackMetadata", {}).get("Item", [])}
                result_code = int(callback.get("ResultCode", -1))
                order_id = str(metadata.get("AccountReference") or callback.get("MerchantRequestID") or "")
                if order_id:
                    try:
                        record_payment(order_id, "PAID" if result_code == 0 else "FAILED")
                    except ValueError:
                        pass
                self.send_text(200, json.dumps({"ResultCode":0,"ResultDesc":"Accepted"}), "application/json")
            except Exception:
                self.send_text(200, json.dumps({"ResultCode":0,"ResultDesc":"Accepted"}), "application/json")
            return
        if parsed.path == "/api/mpesa/stk":
            expected = os.getenv("GROWTH_ADMIN_API_KEY","")
            supplied = self.headers.get("X-Growth-Admin-Key","")
            if not expected or not supplied or not hmac.compare_digest(expected,supplied):
                self.send_text(401,"unauthorized"); return
            try:
                length=int(self.headers.get("Content-Length","0"))
                payload=json.loads(self.rfile.read(length).decode("utf-8"))
                result=stk_push(str(payload.get("phone","")),float(payload.get("amount",0)),str(payload.get("order_id","")))
                self.send_text(200,json.dumps(result,ensure_ascii=False),"application/json")
            except Exception as exc:
                self.send_text(400,json.dumps({"error":str(exc)}),"application/json")
            return
        if parsed.path == "/api/agent/chat":
            try:
                length=int(self.headers.get("Content-Length","0"))
                payload=json.loads(self.rfile.read(length).decode("utf-8"))
                result=agent_chat(str(payload.get("message","")), payload.get("history") or [])
                self.send_text(200,json.dumps(result,ensure_ascii=False),"application/json")
            except ValueError as exc:
                self.send_text(400,json.dumps({"error":str(exc)}),"application/json")
            except Exception:
                self.send_text(500,json.dumps({"error":"agent request failed"}),"application/json")
            return
        if parsed.path == "/api/whatsapp/send":
            expected = os.getenv("GROWTH_ADMIN_API_KEY","")
            supplied = self.headers.get("X-Growth-Admin-Key","")
            if not expected or not supplied or not hmac.compare_digest(expected,supplied):
                self.send_text(401,"unauthorized"); return
            try:
                length=int(self.headers.get("Content-Length","0"))
                payload=json.loads(self.rfile.read(length).decode("utf-8"))
                result=send_text(str(payload.get("to","")),str(payload.get("message","")))
                self.send_text(200,json.dumps(result,ensure_ascii=False),"application/json")
            except Exception as exc:
                self.send_text(400,json.dumps({"error":str(exc)}),"application/json")
            return
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
