"""Growth Stack opportunity engine.

Runs a provider-neutral research loop. It does not browse or contact anyone by itself;
research providers can be plugged in later. Results are scored, deduplicated and queued
for owner review. The design intentionally favors maximum opportunity coverage while
keeping external actions approval-gated.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parent
STATE_DIR = ROOT / "state"
STATE_DIR.mkdir(exist_ok=True)
OPPORTUNITY_FILE = STATE_DIR / "opportunities.json"

M-PESA_NUMBER = "0746352017"
MARKETS = ["Mtwapa", "Kilifi", "Kenya", "East Africa", "Africa", "Global"]
SECTORS = [
    "hotels", "restaurants", "salons", "fashion", "real estate", "tour operators",
    "schools", "NGOs", "professional services", "shops", "events", "creative businesses",
    "online businesses", "SMEs", "health and wellness", "property management",
    "logistics", "education", "hospitality", "travel", "construction", "finance",
]
OPPORTUNITY_TYPES = [
    "AI customer support", "WhatsApp sales", "AI voice receptionist", "lead follow-up",
    "business automation", "AI marketing system", "research-as-a-service",
    "proposal and grant assistance", "document processing", "appointment booking",
    "review/reputation automation", "AI knowledge base", "workflow automation",
    "local-language AI", "Swahili AI", "custom AI agent", "AI implementation",
    "AI safety/security", "data/reporting automation", "micro-SaaS",
]


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_opportunities() -> list[dict[str, Any]]:
    if not OPPORTUNITY_FILE.exists():
        return []
    return json.loads(OPPORTUNITY_FILE.read_text(encoding="utf-8"))


def save_opportunities(items: list[dict[str, Any]]) -> None:
    OPPORTUNITY_FILE.write_text(json.dumps(items, indent=2), encoding="utf-8")


def build_research_queue() -> list[dict[str, str]]:
    """Generate a broad research matrix: market x sector x opportunity type."""
    return [
        {"market": market, "sector": sector, "type": kind}
        for market in MARKETS
        for sector in SECTORS
        for kind in OPPORTUNITY_TYPES
    ]


def score(item: dict[str, Any]) -> float:
    """Base score before live research evidence is added."""
    score = 0.0
    text = f"{item.get('sector','')} {item.get('type','')}".lower()
    if any(x in text for x in ["whatsapp", "follow-up", "booking", "customer support"]):
        score += 2
    if any(x in text for x in ["automation", "agent", "voice"]):
        score += 2
    if item.get("market") in {"Mtwapa", "Kilifi", "Kenya"}:
        score += 1
    if item.get("market") in {"Africa", "Global"}:
        score += 1
    if any(x in text for x in ["research", "proposal", "grant"]):
        score += 1
    return score


def normalize_research(raw: dict[str, Any]) -> dict[str, Any]:
    result = dict(raw)
    result.setdefault("evidence", [])
    result.setdefault("demand_signal", "UNKNOWN")
    result.setdefault("competition", "UNKNOWN")
    result.setdefault("startup_cost", "UNKNOWN")
    result.setdefault("recurring_revenue", "UNKNOWN")
    result.setdefault("ease_of_demo", "UNKNOWN")
    result.setdefault("customer_access", "UNKNOWN")
    result.setdefault("recommended_offer", "")
    result["score"] = float(result.get("score", score(result)))
    result["researched_at"] = now()
    return result


def run_research(provider: Callable[[dict[str, str]], dict[str, Any]] | None = None,
                 limit: int | None = None) -> list[dict[str, Any]]:
    """Research as many queued opportunities as the provider permits.

    provider receives a query descriptor and returns evidence. With no provider this
    creates a complete research queue with transparent UNKNOWN fields rather than
    pretending live research occurred.
    """
    queue = build_research_queue()
    if limit is not None:
        queue = queue[:limit]
    existing = load_opportunities()
    seen = {(x.get("market"), x.get("sector"), x.get("type")) for x in existing}
    for query in queue:
        key = (query["market"], query["sector"], query["type"])
        if key in seen:
            continue
        item = provider(query) if provider else query
        existing.append(normalize_research(item))
    existing.sort(key=lambda x: x.get("score", 0), reverse=True)
    save_opportunities(existing)
    return existing


def top_opportunities(n: int = 20) -> list[dict[str, Any]]:
    return load_opportunities()[:n]


def daily_loop(provider: Callable[[dict[str, str]], dict[str, Any]] | None = None) -> dict[str, Any]:
    results = run_research(provider=provider)
    return {
        "status": "RESEARCH_COMPLETE" if provider else "RESEARCH_QUEUE_READY",
        "queue_size": len(build_research_queue()),
        "stored_opportunities": len(results),
        "top": top_opportunities(10),
        "income_channel": "M-Pesa",
        "income_number": M-PESA_NUMBER,
        "next": "Validate the highest-scoring opportunities with live evidence, then request owner approval for the first offer and outreach batch.",
    }


if __name__ == "__main__":
    report = daily_loop()
    print(json.dumps(report, indent=2))
