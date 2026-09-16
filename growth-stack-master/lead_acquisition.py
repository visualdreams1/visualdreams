"""Growth Stack lead acquisition engine.

Builds evidence-backed prospect records from permitted public business data.
It never guesses contact details, bypasses access controls, or sends outreach.
Outbound delivery remains in sales_autopilot.py behind explicit provider controls.
"""
from __future__ import annotations
import json, os
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
STATE = ROOT / "state"
STATE.mkdir(exist_ok=True)
LEADS = STATE / "leads.json"
QUEUE = STATE / "sales_queue.json"

MIN_SCORE = float(os.getenv("LEAD_MIN_SCORE", "65"))
MAX_LEADS = int(os.getenv("MAX_LEADS_PER_RUN", "100"))
ALLOWED = {"website", "email", "phone", "whatsapp", "linkedin", "contact_page", "social"}


def now(): return datetime.now(timezone.utc).isoformat()
def load(path, default): return json.loads(path.read_text(encoding="utf-8")) if path.exists() else default
def save(path, data): path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def public_contacts(item):
    """Accept only explicitly observed/verified public channels."""
    source = item.get("channels") if item.get("channels") else item.get("public_contacts")
    contacts = []
    seen = set()
    for c in source or []:
        if not isinstance(c, dict): continue
        channel = str(c.get("channel", "")).lower()
        value = str(c.get("value", "")).strip()
        if channel not in ALLOWED or not value: continue
        key = (channel, value.lower())
        if key in seen: continue
        seen.add(key)
        contacts.append({
            "channel": channel,
            "value": value,
            "source_url": clean_url(c.get("source_url")),
            "verification_score": c.get("verification_score", c.get("score"))
        })
    contacts.sort(key=lambda x: float(x.get("verification_score") or 0), reverse=True)
    return contacts


def clean_url(value):
    value = str(value or "").strip()
    return value if value.startswith(("https://", "http://")) else ""


def score_lead(item):
    score = float(item.get("opportunity_score", item.get("score", 0)) or 0)
    text = f"{item.get('sector','')} {item.get('type','')} {item.get('opportunity_type','')} {item.get('pain_signal','')}".lower()
    if any(x in text for x in ("customer support", "whatsapp", "follow-up", "booking")): score += 8
    if any(x in text for x in ("automation", "voice", "agent")): score += 6
    if item.get("verified_business"): score += 8
    if item.get("website"): score += 4
    if public_contacts(item): score += 5
    return round(min(score, 100), 2)


def build_leads(research_items):
    existing = load(LEADS, [])
    by_key = {x.get("lead_key"): x for x in existing if x.get("lead_key")}
    created = 0
    for item in research_items:
        business = str(item.get("business_name", "")).strip()
        if not business: continue
        contacts = public_contacts(item)
        if not contacts: continue
        lead = dict(item)
        lead["public_contacts"] = contacts
        lead["lead_key"] = business.lower() + "|" + str(item.get("market", "")).lower()
        lead["lead_score"] = score_lead(lead)
        lead["score"] = lead["lead_score"]
        lead["status"] = "QUALIFIED" if lead["lead_score"] >= MIN_SCORE else "WATCH"
        lead["updated_at"] = now()
        old = by_key.get(lead["lead_key"])
        if old and old.get("status") in {"DO_NOT_CONTACT", "SUPPRESSED"}:
            lead["status"] = old["status"]
        by_key[lead["lead_key"]] = lead
        if not old: created += 1
        if created >= MAX_LEADS: break
    leads = sorted(by_key.values(), key=lambda x: x.get("lead_score", 0), reverse=True)
    save(LEADS, leads)
    return leads


def create_sales_queue(leads):
    queue = load(QUEUE, [])
    seen = {x.get("lead_key") for x in queue}
    for lead in leads:
        if lead.get("status") not in {"QUALIFIED", "NEW"}: continue
        if lead.get("lead_key") in seen: continue
        contacts = public_contacts(lead)
        if not contacts: continue
        queue.append({
            "lead_key": lead["lead_key"], "business_name": lead.get("business_name"),
            "market": lead.get("market"), "sector": lead.get("sector"),
            "contact": contacts[0], "channels": contacts,
            "score": lead.get("lead_score", 0), "status": "READY_FOR_PERSONALIZATION",
            "created_at": now()
        })
        seen.add(lead["lead_key"])
    save(QUEUE, queue)
    return queue


def run(research_items):
    leads = build_leads(research_items)
    queue = create_sales_queue(leads)
    return {"status":"LEAD_ACQUISITION_COMPLETE", "leads":len(leads), "sales_queue":len(queue)}
