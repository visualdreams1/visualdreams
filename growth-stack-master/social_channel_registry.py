"""Provider-aware social channel registry for Growth Stack Global.

The registry deliberately separates channels that can publish/send through an
approved API from channels that require user interaction or a third-party
connector. No credential, permission, or API capability is invented.
"""
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
STATE = ROOT / "state"
STATE.mkdir(exist_ok=True)

CHANNELS = [
    {"id":"whatsapp","type":"messaging","mode":"api_send_receive","credential_env":["WHATSAPP_PHONE_NUMBER_ID","WHATSAPP_ACCESS_TOKEN"],"status":"provider_gated"},
    {"id":"facebook_messenger","type":"messaging","mode":"api_send_receive","status":"provider_gated"},
    {"id":"instagram","type":"social_messaging","mode":"api_send_receive","status":"provider_gated"},
    {"id":"linkedin","type":"professional_social","mode":"api_access_varies","status":"approval_or_partner_gated"},
    {"id":"tiktok","type":"social","mode":"api_capabilities_vary","status":"approval_and_scope_gated"},
    {"id":"x","type":"social_messaging","mode":"api_access_varies","status":"provider_gated"},
    {"id":"youtube","type":"social","mode":"api_publish_and_manage","status":"oauth_gated"},
    {"id":"telegram","type":"messaging","mode":"bot_api","status":"credential_gated"},
    {"id":"reddit","type":"community","mode":"api_access_varies","status":"provider_gated"},
    {"id":"email","type":"owned_channel","mode":"smtp_or_provider_api","status":"credential_gated"},
    {"id":"website_chat","type":"owned_channel","mode":"webhook","status":"deployable"},
]


def write_registry():
    payload = {
        "purpose":"one sales brain, many authorized channels",
        "channels":CHANNELS,
        "rules":[
            "Use official APIs or authorized integrations only.",
            "Respect each platform's messaging, automation, rate and consent rules.",
            "Never scrape around access controls, bypass CAPTCHA, or impersonate users.",
            "Track every outbound event and opt-out.",
            "A social channel can generate leads; payment confirmation happens through an authorized payment provider.",
        ],
    }
    (STATE/"social_channel_registry.json").write_text(json.dumps(payload,indent=2),encoding="utf-8")
    return payload

if __name__ == "__main__":
    print(json.dumps(write_registry(),indent=2))
