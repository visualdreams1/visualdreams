"""Permission-aware social account control plane.

Credentials stay in Render secrets. This module stores policy only.
"""
from __future__ import annotations
import os

ACTIONS = (
    "read_profile", "read_business_messages", "read_insights",
    "draft_content", "publish_content", "reply_to_messages",
    "qualify_inbound_leads", "follow_up_authorized_contacts",
    "create_payment_request_after_buyer_intent",
)
RESTRICTED = (
    "change_password", "change_security_settings", "delete_account",
    "spend_money", "bypass_platform_controls",
)
CHANNELS = {
    "whatsapp": ["WHATSAPP_PHONE_NUMBER_ID", "WHATSAPP_ACCESS_TOKEN"],
    "messenger": ["META_PAGE_ACCESS_TOKEN"],
    "instagram": ["META_PAGE_ACCESS_TOKEN"],
    "linkedin": ["LINKEDIN_ACCESS_TOKEN"],
    "x": ["X_API_KEY", "X_API_SECRET", "X_ACCESS_TOKEN", "X_ACCESS_TOKEN_SECRET"],
    "tiktok": ["TIKTOK_ACCESS_TOKEN"],
    "telegram": ["TELEGRAM_BOT_TOKEN"],
    "reddit": ["REDDIT_CLIENT_ID", "REDDIT_CLIENT_SECRET", "REDDIT_REFRESH_TOKEN"],
    "email": ["SMTP_HOST", "SMTP_USERNAME", "SMTP_PASSWORD"],
    "youtube": ["YOUTUBE_ACCESS_TOKEN"],
}

def status() -> dict:
    accounts = {}
    for channel, envs in CHANNELS.items():
        accounts[channel] = {
            "credentials_configured": bool(envs) and all(os.getenv(k) for k in envs),
            "owner_authorization_required": True,
            "permissions": list(ACTIONS),
            "restricted_actions": list(RESTRICTED),
            "connection_method": "official_api_or_approved_connector",
        }
    return {
        "mode": "permissioned_social_control_plane",
        "owner_authorization": "required_per_account",
        "credential_handling": "deployment_secrets_only",
        "accounts": accounts,
        "outbound_default": False,
        "rules": [
            "Use official APIs or approved connectors only.",
            "Never request or store account passwords in chat.",
            "Never bypass rate limits, authentication, platform rules or opt-outs.",
            "Only contact authorized or legitimately engaged recipients.",
            "Log external actions and preserve an audit trail.",
            "Escalate security, privacy, legal and financial exceptions.",
        ],
    }

if __name__ == "__main__":
    import json
    print(json.dumps(status(), indent=2))
