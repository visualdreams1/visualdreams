"""Run the autonomous Growth Stack intelligence, sales and revenue pipeline."""
from __future__ import annotations
import json
from autonomous_health import main as health_main
from live_research import research_worldwide
from business_discovery import discover
from contact_verifier import verify
from intelligence_engine import build_queue
from multichannel_intelligence import run as multichannel
from lead_acquisition import run as acquire_leads
from sales_autopilot import autopilot
from outcome_engine import process_replies, metrics
from response_engine import run as draft_responses
from payment_engine import reconcile as reconcile_payments
from revenue_loop import run as revenue_loop
from monitor import check

def main():
    health_main()
    opportunities=research_worldwide(limit=250)
    intel=build_queue()
    discovered=discover(opportunities)
    verified=verify(discovered)
    multi=multichannel(verified)
    leads=acquire_leads(verified)
    sales=autopilot()
    outcomes=process_replies()
    responses=draft_responses()
    payments=reconcile_payments()
    revenue=revenue_loop()
    sales_metrics=metrics()
    monitor=check()
    print(json.dumps({"research":"complete","intelligence":intel,"business_discovery":{"businesses":len(discovered)},"contact_verification":{"leads":len(verified),"with_contacts":sum(bool(x.get("channels")) for x in verified)},"multichannel":multi,"lead_acquisition":leads,"sales":sales,"outcomes":outcomes,"responses":responses,"payments":payments,"revenue":revenue,"sales_metrics":sales_metrics,"monitor":monitor},indent=2))

if __name__=="__main__":main()
