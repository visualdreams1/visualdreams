"""Growth Stack Global agent team registry and revenue mission planner.

Agents are bounded specialists. They share a single mission, state directory,
customer evidence, and revenue scorecard. This module does not invent leads,
contacts, payments, or customer results.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
STATE = ROOT / "state"
STATE.mkdir(exist_ok=True)

TARGET = int(os.getenv("MILLION_TARGET_KES", "1000000"))

AGENTS = [
    {"id": "ceo", "role": "CEO/Strategy", "mission": "Choose the highest-value evidence-backed commercial path."},
    {"id": "scout", "role": "Opportunity Scout", "mission": "Find real business problems with public evidence and buying signals."},
    {"id": "research", "role": "Research Intelligence", "mission": "Validate market, vertical, pain, competitor and timing evidence."},
    {"id": "offer", "role": "Offer Architect", "mission": "Turn a verified problem into a concrete AI implementation offer and price."},
    {"id": "prospector", "role": "Prospecting", "mission": "Identify legitimate public business contacts; never guess contact details."},
    {"id": "sales", "role": "Sales Agent", "mission": "Personalize concise outreach, qualify interest and move leads to a demo/proposal."},
    {"id": "followup", "role": "Follow-up Agent", "mission": "Follow up only when permitted and suppress STOP/negative responses."},
    {"id": "solution", "role": "Solutions Engineer", "mission": "Assemble the smallest working AI system that can demonstrate business value."},
    {"id": "demo", "role": "Demo Factory", "mission": "Generate vertical-specific demos and proof-of-value assets."},
    {"id": "customer_success", "role": "Customer Success", "mission": "Onboard, measure outcomes, retain and identify legitimate expansion opportunities."},
    {"id": "finance", "role": "Finance", "mission": "Track quotes, confirmed payments, revenue, AI cost and gross margin."},
    {"id": "risk", "role": "Risk/Governance", "mission": "Protect privacy, permissions, opt-outs, provider rules and auditability."},
    {"id": "optimizer", "role": "Growth Optimizer", "mission": "Learn from funnel outcomes and reallocate effort toward measured conversion."},
]


def now():
    return datetime.now(timezone.utc).isoformat()


def build_mission():
    return {
        "mission": "Reach the first KES 1,000,000 in confirmed business revenue through real customer value.",
        "target_kes": TARGET,
        "started_at": now(),
        "operator": "Dennis Achege / Growth Stack Global",
        "principles": [
            "Sell outcomes, not AI features.",
            "Prefer high-value B2B implementations over many tiny transactions.",
            "Use evidence before scaling a vertical or offer.",
            "No fabricated leads, identities, payments, testimonials or results.",
            "Respect opt-outs and provider/platform rules.",
            "Every paid project should create reusable proof and a repeatable product.",
        ],
        "team": AGENTS,
        "commercial_ladder": [
            {"name": "AI Revenue Audit", "price_kes": 5000, "purpose": "paid diagnostic and entry point"},
            {"name": "AI Employee Starter", "price_kes": 25000, "purpose": "single workflow implementation"},
            {"name": "AI Business System", "price_kes": 75000, "purpose": "multi-workflow implementation"},
            {"name": "AI Growth Operating System", "price_kes": 150000, "purpose": "sales + service + operations automation"},
            {"name": "Enterprise AI Implementation", "price_kes": 250000, "purpose": "larger implementation; scope-based"},
        ],
        "million_paths": [
            "4 x KES 250,000 implementations",
            "7 x KES 150,000 implementations",
            "14 x KES 75,000 implementations",
        ],
        "today_priority": [
            "Generate a high-confidence prospect queue.",
            "Package one irresistible, demonstrable offer per tested vertical.",
            "Run compliant personalized outreach where provider credentials permit it.",
            "Convert positive replies into demos/proposals and confirmed deposits.",
        ],
    }


def main():
    mission = build_mission()
    (STATE / "agent_team.json").write_text(json.dumps(mission, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(mission, indent=2))
    return mission


if __name__ == "__main__":
    main()
