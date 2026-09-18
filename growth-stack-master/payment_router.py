"""Payment provider readiness layer.

Keeps payment collection provider-gated: no payment is marked paid without a
verified provider callback/transaction record.
"""
from __future__ import annotations
import json, os
from pathlib import Path

ROOT = Path(__file__).resolve().parent

PROVIDERS = {
    "mpesa_daraja": [
        "MPESA_DARAJA_BASE_URL",
        "MPESA_CONSUMER_KEY",
        "MPESA_CONSUMER_SECRET",
        "MPESA_SHORTCODE",
        "MPESA_PASSKEY",
    ],
    "stripe": ["STRIPE_SECRET_KEY"],
    "paypal": ["PAYPAL_CLIENT_ID", "PAYPAL_CLIENT_SECRET"],
}


def readiness():
    return {
        p: {"configured": all(os.getenv(k) for k in keys), "missing": [k for k in keys if not os.getenv(k)]}
        for p, keys in PROVIDERS.items()
    }


def main():
    r = {"providers": readiness(), "currency": "KES", "collection_account_configured": bool(os.getenv("MPESA_NUMBER")),
         "rule": "only verified provider callbacks can mark an order PAID"}
    r["connected_count"] = sum(x["configured"] for x in r["providers"].values())
    (ROOT / "state" / "payment_readiness.json").write_text(json.dumps(r, indent=2), encoding="utf-8")
    return r

if __name__ == "__main__":
    print(json.dumps(main(), indent=2))
