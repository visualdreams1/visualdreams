"""Direct Meta WhatsApp Cloud API sender for Growth Stack.

No secrets are stored in the repository. Configure environment variables:
WHATSAPP_CLOUD_API_VERSION, WHATSAPP_PHONE_NUMBER_ID,
WHATSAPP_ACCESS_TOKEN.
For proactive business-initiated outreach, configure an approved template with
WHATSAPP_TEMPLATE_NAME and WHATSAPP_TEMPLATE_LANGUAGE. Free-form text is used
only when explicitly selected with WHATSAPP_ALLOW_FREEFORM=true.
"""
from __future__ import annotations
import json, os, urllib.error, urllib.request


def configured() -> bool:
    return bool(os.getenv("WHATSAPP_PHONE_NUMBER_ID") and os.getenv("WHATSAPP_ACCESS_TOKEN"))


def _url() -> str:
    version = os.getenv("WHATSAPP_CLOUD_API_VERSION", "v23.0")
    phone_id = os.environ["WHATSAPP_PHONE_NUMBER_ID"]
    return f"https://graph.facebook.com/{version}/{phone_id}/messages"


def _post(body: dict) -> dict:
    req = urllib.request.Request(
        _url(),
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {os.environ['WHATSAPP_ACCESS_TOKEN']}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            raw = response.read().decode("utf-8")
            return {"ok": 200 <= response.status < 300, "status": response.status, "body": json.loads(raw) if raw else {}}
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        return {"ok": False, "status": exc.code, "body": raw[:2000]}
    except Exception as exc:
        return {"ok": False, "status": 0, "body": str(exc)[:500]}


def send_text(to: str, message: str) -> dict:
    if not configured():
        return {"ok": False, "status": 0, "body": "WhatsApp Cloud API is not configured"}
    body = {"messaging_product": "whatsapp", "to": to, "type": "text", "text": {"preview_url": False, "body": message}}
    return _post(body)


def send_template(to: str, template_name: str, language: str = "en_US", parameters: list[str] | None = None) -> dict:
    if not configured():
        return {"ok": False, "status": 0, "body": "WhatsApp Cloud API is not configured"}
    parameters = parameters or []
    components = []
    if parameters:
        components.append({"type": "body", "parameters": [{"type": "text", "text": str(x)} for x in parameters]})
    body = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "template",
        "template": {"name": template_name, "language": {"code": language}},
    }
    if components:
        body["template"]["components"] = components
    return _post(body)


def send(to: str, message: str, template_parameters: list[str] | None = None) -> dict:
    template = os.getenv("WHATSAPP_TEMPLATE_NAME", "").strip()
    language = os.getenv("WHATSAPP_TEMPLATE_LANGUAGE", "en_US")
    if template:
        return send_template(to, template, language, template_parameters or [])
    if os.getenv("WHATSAPP_ALLOW_FREEFORM", "false").lower() in {"1", "true", "yes"}:
        return send_text(to, message)
    return {"ok": False, "status": 0, "body": "No approved WhatsApp template configured and freeform sending is disabled"}
