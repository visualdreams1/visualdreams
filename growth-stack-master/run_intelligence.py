"""Run research, intelligence, lead acquisition, sales queue and monitoring."""
from __future__ import annotations
import json
from live_research import research_worldwide
from intelligence_engine import build_queue
from lead_acquisition import run as acquire_leads
from sales_autopilot import autopilot
from monitor import check


def main():
    opportunities = research_worldwide(limit=250)
    intel = build_queue()
    # Lead acquisition only promotes records that contain provider-supplied,
    # permitted public business contact data; it never invents contacts.
    leads = acquire_leads(opportunities)
    sales = autopilot()
    monitor = check()
    print(json.dumps({"research":"complete","intelligence":intel,"lead_acquisition":leads,"sales":sales,"monitor":monitor},indent=2))

if __name__ == "__main__":
    main()
