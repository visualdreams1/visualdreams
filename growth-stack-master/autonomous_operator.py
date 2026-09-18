"""Growth Stack Global autonomous revenue operator."""
from __future__ import annotations
import json, os, time
from datetime import datetime, timezone
from pathlib import Path

from autonomous_health import main as health_main
from live_research import research_worldwide
from business_discovery import discover
from contact_verifier import verify
from intelligence_engine import build_queue
from multichannel_intelligence import run as multichannel
from lead_acquisition import run as acquire_leads
from sales_autopilot import autopilot
from outcome_engine import process_replies, metrics as sales_metrics
from response_engine import run as draft_responses
from payment_engine import reconcile as reconcile_payments
from revenue_loop import run as revenue_loop
from adaptive_strategy import run as adaptive_run
from monitor import check
from agent_team import main as build_agent_team
from offer_engine import run as build_offers
from channel_router import main as channel_readiness
from payment_router import main as payment_readiness
from autonomy_constitution import load as autonomy_constitution

ROOT = Path(__file__).resolve().parent
STATE = ROOT / "state"
STATE.mkdir(exist_ok=True)
CYCLE_COUNT = max(1, min(int(os.getenv("OPERATOR_CYCLES", "1")), 3))
RESEARCH_LIMIT = max(50, min(int(os.getenv("OPERATOR_RESEARCH_LIMIT", "250")), 500))

def now(): return datetime.now(timezone.utc).isoformat()
def save_run(report):
    (STATE / "operator_last_run.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

def cycle(index):
    started = now(); constitution = autonomy_constitution()
    if os.getenv("GROWTH_KILL_SWITCH","false").lower() in {"1","true","yes"}:
        report = {"cycle": index, "started_at": started, "finished_at": now(), "status": "KILL_SWITCH_ACTIVE", "constitution": constitution["version"]}
        save_run(report); return report
    health = health_main(); team = build_agent_team()
    channels = channel_readiness(); payments_ready = payment_readiness(); research_error = None
    try: opportunities = research_worldwide(limit=RESEARCH_LIMIT)
    except Exception as exc:
        opportunities = []; research_error = f"{type(exc).__name__}: {exc}"
        (STATE / "operator_provider_error.json").write_text(json.dumps({"at": now(), "stage": "research", "error": research_error}, indent=2), encoding="utf-8")
    intelligence = build_queue(); discovered = discover(opportunities); verified = verify(discovered)
    multi = multichannel(verified); leads = acquire_leads(verified); offers = build_offers(verified)
    outcomes = process_replies(); responses = draft_responses(); sales = autopilot()
    payment_result = reconcile_payments(); revenue = revenue_loop(); sm = sales_metrics(); adaptive = adaptive_run(); monitor = check()
    return {"cycle": index, "started_at": started, "finished_at": now(), "health": health,
            "agent_team": {"agents": len(team.get("team", [])), "target_kes": team.get("target_kes")},
            "channel_readiness": channels, "payment_readiness": payments_ready,
            "research": {"opportunities": len(opportunities), "error": research_error}, "intelligence": intelligence,
            "discovery": {"businesses": len(discovered)}, "verification": {"leads": len(verified), "with_contacts": sum(bool(x.get("channels")) for x in verified)},
            "multichannel": multi, "lead_acquisition": leads, "offers": {"generated": offers.get("count", 0)},
            "outcomes": outcomes, "responses": responses, "sales": sales, "payments": payment_result,
            "revenue": revenue, "sales_metrics": sm, "adaptive": adaptive, "monitor": monitor}

def main():
    reports = []
    for i in range(1, CYCLE_COUNT + 1):
        reports.append(cycle(i))
        if i < CYCLE_COUNT: time.sleep(max(0, int(os.getenv("OPERATOR_CYCLE_DELAY_SECONDS", "5"))))
    report = {"operator": "GROWTH_STACK_AUTONOMOUS_REVENUE_OPERATOR", "version": "2.1-multichannel-payments",
              "mission": "discover customers, sell, deliver, reconcile verified payments and learn", "million_target_kes": int(os.getenv("MILLION_TARGET_KES", "1000000")),
              "autonomy": "exception_only", "approval_gates": "SAFETY_AND_EXCEPTION_GATES", "constitution_version": "3.0", "external_outreach_enabled": os.getenv("OUTBOUND_ENABLED", "false").lower() == "true",
              "payment_provider_connected": bool(os.getenv("MPESA_DARAJA_BASE_URL") and os.getenv("MPESA_CONSUMER_KEY")), "cycles": reports, "finished_at": now()}
    save_run(report); print(json.dumps(report, indent=2))

if __name__ == "__main__": main()
