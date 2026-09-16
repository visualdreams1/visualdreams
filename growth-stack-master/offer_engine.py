"""Evidence-based offer and million-target planner.

Creates commercial options from verified lead evidence. It never claims a result
before payment or delivery evidence exists.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent
STATE = ROOT / "state"
STATE.mkdir(exist_ok=True)

OFFERS = {
    "hotel": {"name": "AI WhatsApp Revenue Desk", "price": 75000, "outcome": "capture enquiries, answer FAQs, qualify guests and recover follow-ups"},
    "tour": {"name": "AI Booking & Follow-up Agent", "price": 75000, "outcome": "respond to trip enquiries, qualify leads and follow up"},
    "real_estate": {"name": "AI Property Lead Agent", "price": 75000, "outcome": "qualify property enquiries and route serious buyers"},
    "school": {"name": "AI Admissions & Parent Desk", "price": 50000, "outcome": "answer admissions questions and organize enquiries"},
    "salon": {"name": "AI Booking & Customer Care Agent", "price": 25000, "outcome": "handle bookings, FAQs and follow-up"},
    "fashion": {"name": "AI Sales Concierge", "price": 25000, "outcome": "turn product enquiries into qualified sales conversations"},
    "default": {"name": "AI Business Revenue Audit + Agent", "price": 25000, "outcome": "identify one revenue leak and automate the highest-value workflow"},
}


def normalize_vertical(value: str) -> str:
    v = (value or "").lower().replace("-", "_").replace(" ", "_")
    aliases = {"hotels": "hotel", "tourism": "tour", "tour_operator": "tour", "realestate": "real_estate", "real_estate": "real_estate"}
    return aliases.get(v, v)


def make_offer(lead: dict) -> dict:
    vertical = normalize_vertical(lead.get("sector") or lead.get("vertical") or "default")
    offer = OFFERS.get(vertical, OFFERS["default"])
    evidence = lead.get("evidence") or lead.get("signals") or []
    return {
        "business": lead.get("business") or lead.get("name"),
        "website": lead.get("website"),
        "vertical": vertical,
        "offer": offer["name"],
        "price_kes": offer["price"],
        "proposed_outcome": offer["outcome"],
        "evidence_count": len(evidence) if isinstance(evidence, list) else 0,
        "status": "DRAFT_PROPOSAL",
    }


def million_gap(confirmed_revenue_kes: int = 0) -> dict:
    target = int(os.getenv("MILLION_TARGET_KES", "1000000"))
    gap = max(0, target - int(confirmed_revenue_kes))
    return {"target_kes": target, "confirmed_revenue_kes": int(confirmed_revenue_kes), "gap_kes": gap}


def run(leads=None):
    leads = leads or []
    offers = [make_offer(x) for x in leads]
    output = {"offers": offers, "million_target": million_gap(), "count": len(offers)}
    (STATE / "offer_queue.json").write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")
    return output


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
