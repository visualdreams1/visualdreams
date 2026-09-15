"""Run the autonomous Growth Stack intelligence and sales pipeline."""
from __future__ import annotations
import json
from live_research import research_worldwide
from business_discovery import discover
from intelligence_engine import build_queue
from multichannel_intelligence import run as multichannel
from lead_acquisition import run as acquire_leads
from sales_autopilot import autopilot
from monitor import check


def main():
    opportunities = research_worldwide(limit=250)
    intel = build_queue()
    discovered = discover(opportunities)
    multi = multichannel(discovered)
    leads = acquire_leads(discovered)
    sales = autopilot()
    monitor = check()
    print(json.dumps({
        "research":"complete","intelligence":intel,
        "business_discovery":{"businesses":len(discovered)},
        "multichannel":multi,"lead_acquisition":leads,
        "sales":sales,"monitor":monitor
    },indent=2))

if __name__ == "__main__":
    main()
