"""Provider-neutral channel readiness and routing for Growth Stack Global.

This layer never bypasses platform controls. It selects only channels that are
explicitly configured and marked send-capable by the registry.
"""
from __future__ import annotations
import json, os
from pathlib import Path

ROOT = Path(__file__).resolve().parent

CHANNELS = {
    "whatsapp": {"env": ["WHATSAPP_PHONE_NUMBER_ID", "WHATSAPP_ACCESS_TOKEN"], "mode": "api"},
    "messenger": {"env": ["META_PAGE_ACCESS_TOKEN"], "mode": "api"},
    "instagram": {"env": ["META_PAGE_ACCESS_TOKEN"], "mode": "api"},
    "linkedin": {"env": ["LINKEDIN_ACCESS_TOKEN"], "mode": "approved_api"},
    "x": {"env": ["X_API_KEY", "X_API_SECRET", "X_ACCESS_TOKEN", "X_ACCESS_TOKEN_SECRET"], "mode": "approved_api"},
    "tiktok": {"env": ["TIKTOK_ACCESS_TOKEN"], "mode": "approved_api"},
    "telegram": {"env": ["TELEGRAM_BOT_TOKEN"], "mode": "bot_api"},
    "reddit": {"env": ["REDDIT_CLIENT_ID", "REDDIT_CLIENT_SECRET", "REDDIT_REFRESH_TOKEN"], "mode": "approved_api"},
    "email": {"env": ["SMTP_HOST", "SMTP_USERNAME", "SMTP_PASSWORD"], "mode": "smtp"},
    "website": {"env": [], "mode": "webhook"},
    "youtube": {"env": ["YOUTUBE_ACCESS_TOKEN"], "mode": "oauth_publish"},
}


def readiness():
    out = {}
    for name, spec in CHANNELS.items():
        missing = [k for k in spec["env"] if not os.getenv(k)]
        out[name] = {
            "configured": not missing,
            "missing_credentials": missing,
            "mode": spec["mode"],
            "send_enabled": os.getenv(f"{name.upper()}_OUTBOUND_ENABLED", "false").lower() == "true",
        }
    return out


def rank(lead):
    channels = lead.get("channels", {}) if isinstance(lead, dict) else {}
    ready = readiness()
    order = ["whatsapp", "messenger", "instagram", "linkedin", "x", "tiktok", "telegram", "email", "reddit", "website"]
    ranked = []
    for ch in order:
        if channels.get(ch) and ready[ch]["configured"] and ready[ch]["send_enabled"]:
            ranked.append(ch)
    return ranked


def main():
    result = {"channels": readiness(), "policy": "authorized_api_only_no_spam_no_bypass", "ready_count": 0}
    result["ready_count"] = sum(1 for x in result["channels"].values() if x["configured"] and x["send_enabled"])
    (ROOT / "state" / "channel_readiness.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result

if __name__ == "__main__":
    print(json.dumps(main(), indent=2))
