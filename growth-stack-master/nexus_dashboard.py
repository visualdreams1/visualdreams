"""NEXUS command dashboard for Growth Stack Global.

Read-only presentation layer. It exposes commercial summaries without exposing
raw CRM records, secrets, payment records, or message contents.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from growth_core import executive_status

ROOT = Path(__file__).resolve().parent
STATE = ROOT / "state"


def load(name: str, default):
    path = STATE / name
    try:
        return json.loads(path.read_text(encoding="utf-8")) if path.exists() else default
    except Exception:
        return default


def summary() -> dict:
    operator = load("operator_last_run.json", {})
    health = load("health.json", {})
    commercial = executive_status()
    channels = load("channel_readiness.json", {})
    leads = load("leads.json", [])
    sales_queue = load("sales_queue.json", [])
    payment_state = load("payments.json", [])
    cycles = operator.get("cycles") or []
    latest = cycles[-1] if cycles else {}
    research = latest.get("research", {})
    discovery = latest.get("discovery", {})
    verification = latest.get("verification", {})
    metrics = latest.get("sales_metrics", {}) or {}
    ready_channels = [name for name, value in (channels.get("channels") or {}).items()
                      if isinstance(value, dict) and value.get("ready")]
    paid_count = sum(1 for x in payment_state if isinstance(x, dict) and x.get("status") == "PAID")
    return {
        "product": "Growth Stack Global — NEXUS",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": health.get("status", "NOT_RUN"),
        "mission": "Find, qualify, sell, deliver, verify payment, learn.",
        "target_kes": operator.get("million_target_kes", 1_000_000),
        "research_opportunities": research.get("opportunities", 0),
        "discovered_businesses": discovery.get("businesses", 0),
        "verified_leads": verification.get("leads", 0),
        "contacts": verification.get("with_contacts", 0),
        "sales_queue": len(sales_queue) if isinstance(sales_queue, list) else 0,
        "total_leads": len(leads) if isinstance(leads, list) else 0,
        "paid_orders": paid_count,
        "sales_metrics": metrics,
        "external_outreach_enabled": bool(operator.get("external_outreach_enabled")),
        "ready_channels": ready_channels,
        "payment_provider_connected": bool(operator.get("payment_provider_connected")),
        "manual_mpesa": os.getenv("MPESA_NUMBER", "0746352017"),
        "research_error": research.get("error"),
        "warnings": health.get("warnings", []),
        "commercial": commercial,
        "revenue_kes": commercial.get("revenue_kes", 0),
        "revenue_usd": commercial.get("revenue_usd", 0),
    }


def html_page(data: dict) -> str:
    import html
    esc = lambda value: html.escape(str(value))
    cards = [("Status", data["status"]), ("Global opportunities", data["research_opportunities"]),
             ("Businesses", data["discovered_businesses"]), ("Qualified leads", data["verified_leads"]),
             ("Sales queue", data["sales_queue"]), ("Paid orders", data["paid_orders"]),
             ("KES revenue", data["revenue_kes"]), ("USD revenue", data["revenue_usd"])]
    card_html = "".join(f'<div class="card"><span>{esc(k)}</span><strong>{esc(v)}</strong></div>' for k, v in cards)
    channels = ", ".join(data["ready_channels"]) if data["ready_channels"] else "None connected"
    error = f'<div class="warning">Research: {esc(data["research_error"])}</div>' if data.get("research_error") else ""
    warnings = "".join(f'<li>{esc(x)}</li>' for x in data.get("warnings", [])) or "<li>None</li>"
    outbound = "ENABLED" if data["external_outreach_enabled"] else "APPROVAL / PROVIDER GATED"
    payments = "PROVIDER CONNECTED" if data["payment_provider_connected"] else "MANUAL M-PESA AVAILABLE"
    return f'''<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>NEXUS — Growth Stack Global</title><style>
body{{margin:0;background:#070b14;color:#eef2ff;font-family:system-ui,-apple-system,sans-serif}}main{{max-width:1100px;margin:auto;padding:28px}}
h1{{font-size:32px;margin:0}}.sub{{color:#9ca8c4;margin:6px 0 28px}}.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px}}
.card{{background:#101827;border:1px solid #263248;border-radius:16px;padding:18px}}.card span{{display:block;color:#94a3b8;font-size:13px}}.card strong{{display:block;font-size:28px;margin-top:7px}}
.panel{{background:#0d1421;border:1px solid #263248;border-radius:18px;padding:20px;margin-top:16px}}.ok{{color:#5eead4}}.warning{{background:#422006;color:#fed7aa;padding:12px;border-radius:10px;margin-top:12px}}.label{{color:#94a3b8;font-size:13px}}code{{color:#c4b5fd}}
</style></head><body><main><h1>⚡ NEXUS</h1><div class="sub">Growth Stack Global — Autonomous Revenue Command</div>
<div class="grid">{card_html}</div><div class="panel"><div class="label">MISSION</div><p>{esc(data["mission"])}</p>
<div class="label">REVENUE TARGET</div><p>KES {data["target_kes"]:,}</p><div class="label">READY CHANNELS</div><p class="ok">{esc(channels)}</p>
<div class="label">OUTBOUND</div><p>{outbound}</p><div class="label">PAYMENTS</div><p>{payments}</p></div>{error}
<div class="panel"><div class="label">SYSTEM WARNINGS</div><ul>{warnings}</ul></div>
<div class="panel"><div class="label">LAST UPDATED</div><p>{esc(data["timestamp"])}</p><p>JSON endpoint: <code>/api/nexus</code></p></div>
</main></body></html>'''
