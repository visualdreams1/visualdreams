"""Provider-neutral commercial engine for Growth Stack Global.

This module deliberately avoids WhatsApp, payment-provider SDKs, and AI-provider
credentials. It provides the reusable business layer that channels can call later:
catalog, pricing, CRM, order ledger, and executive metrics.
"""
from __future__ import annotations

import json
import os
import secrets
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
STATE = ROOT / "state"
STATE.mkdir(exist_ok=True)

CATALOG = {
    "P01": {
        "name": "WhatsApp AI Employee",
        "outcome": "Automated first-line customer support and lead capture",
        "delivery_days": 3,
        "kenya_price_kes": 1500,
        "international_price_usd": 49,
        "recurring_usd": 29,
    },
    "P02": {
        "name": "AI Customer Support Agent",
        "outcome": "Faster customer replies with escalation to a human",
        "delivery_days": 3,
        "kenya_price_kes": 2500,
        "international_price_usd": 79,
        "recurring_usd": 39,
    },
    "P03": {
        "name": "AI Sales Agent",
        "outcome": "Lead qualification, follow-up and pipeline organization",
        "delivery_days": 5,
        "kenya_price_kes": 5000,
        "international_price_usd": 149,
        "recurring_usd": 59,
    },
    "P05": {
        "name": "AI Business Automation",
        "outcome": "Automate repetitive business workflows",
        "delivery_days": 7,
        "kenya_price_kes": 7500,
        "international_price_usd": 249,
        "recurring_usd": 99,
    },
    "P07": {
        "name": "AI Research & Intelligence",
        "outcome": "Decision-ready market and competitor research",
        "delivery_days": 2,
        "kenya_price_kes": 1500,
        "international_price_usd": 49,
        "recurring_usd": 0,
    },
    "P08": {
        "name": "AI Proposal & Funding Desk",
        "outcome": "Professional proposals, plans, decks and reports",
        "delivery_days": 2,
        "kenya_price_kes": 1500,
        "international_price_usd": 49,
        "recurring_usd": 0,
    },
}

def now() -> str:
    return datetime.now(timezone.utc).isoformat()

def _read(name: str, default: Any) -> Any:
    path = STATE / name
    try:
        return json.loads(path.read_text(encoding="utf-8")) if path.exists() else default
    except Exception:
        return default

def _write(name: str, value: Any) -> None:
    tmp = STATE / (name + ".tmp")
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(STATE / name)

def products() -> list[dict]:
    return [{"product_id": k, **v} for k, v in CATALOG.items()]

def quote(product_id: str, market: str = "KE") -> dict:
    product = CATALOG.get(product_id.upper())
    if not product:
        raise ValueError("Unknown product")
    market = (market or "KE").upper()
    if market in {"KE", "KENYA"}:
        return {
            "product_id": product_id.upper(),
            "name": product["name"],
            "currency": "KES",
            "price": max(1500, int(product["kenya_price_kes"])),
            "recurring": None,
            "delivery_days": product["delivery_days"],
            "outcome": product["outcome"],
        }
    return {
        "product_id": product_id.upper(),
        "name": product["name"],
        "currency": "USD",
        "price": float(product["international_price_usd"]),
        "recurring": float(product["recurring_usd"]) if product["recurring_usd"] else None,
        "delivery_days": product["delivery_days"],
        "outcome": product["outcome"],
    }

def add_lead(data: dict) -> dict:
    leads = _read("leads.json", [])
    lead = {
        "lead_id": "L-" + secrets.token_hex(6),
        "created_at": now(),
        "stage": "RESEARCHED",
        "contact_status": "UNKNOWN",
        "next_action": "QUALIFY",
        **{k: data.get(k) for k in (
            "contact_name", "business", "vertical", "location",
            "contact_channel", "problem", "consent"
        )},
    }
    leads.append(lead)
    _write("leads.json", leads)
    return lead

def create_order(data: dict) -> dict:
    product_id = str(data.get("product_id", "")).upper()
    market = str(data.get("market", "KE")).upper()
    customer = str(data.get("customer", "")).strip()
    if not product_id or not customer:
        raise ValueError("product_id and customer are required")
    pricing = quote(product_id, market)
    orders = _read("commercial_orders.json", [])
    order = {
        "order_id": "GS-" + secrets.token_hex(6),
        "created_at": now(),
        "status": "PENDING_PAYMENT",
        "payment_status": "UNPAID",
        "customer": customer,
        "contact": data.get("contact"),
        "market": market,
        "pricing": pricing,
    }
    orders.append(order)
    _write("commercial_orders.json", orders)
    return order

def record_payment(order_id: str, status: str = "PAID") -> dict:
    orders = _read("orders.json", [])
    status = status.upper()
    for order in orders:
        if order.get("order_id") == order_id:
            order["payment_status"] = status
            order["status"] = "PAID" if status == "PAID" else "PAYMENT_REVIEW"
            order["payment_updated_at"] = now()
            _write("orders.json", orders)
            return order
    raise ValueError("Order not found")

def executive_status() -> dict:
    leads = _read("leads.json", [])
    orders = _read("orders.json", [])
    paid = [o for o in orders if o.get("payment_status") == "PAID"]
    revenue_kes = sum(
        float(o.get("pricing", {}).get("price", 0))
        for o in paid if o.get("pricing", {}).get("currency") == "KES"
    )
    revenue_usd = sum(
        float(o.get("pricing", {}).get("price", 0))
        for o in paid if o.get("pricing", {}).get("currency") == "USD"
    )
    return {
        "timestamp": now(),
        "status": "OPERATIONAL",
        "mission": "Find, qualify, sell, deliver, verify payment, learn.",
        "target_kes": 1_000_000,
        "products": len(CATALOG),
        "leads": len(leads),
        "orders": len(orders),
        "paid_orders": len(paid),
        "revenue_kes": revenue_kes,
        "revenue_usd": revenue_usd,
        "whatsapp_connected": False,
        "payment_provider_connected": False,
        "next_layer": "Connect channels and payment providers after the core is validated.",
    }
