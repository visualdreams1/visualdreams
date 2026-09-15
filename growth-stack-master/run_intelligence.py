"""Run the autonomous Growth Stack intelligence and sales pipeline."""
from __future__ import annotations
import json
from live_research import research_worldwide
from business_discovery import discover
from contact_verifier import verify
from intelligence_engine import build_queue
from multichannel_intelligence import run as multichannel
from lead_acquisition import run as acquire_leads
from sales_autopilot import autopilot
from monitor import check
from outcome_engine import process_replies, metrics

def main():
    opportunities=research_worldwide(limit=250)
    intel=build_queue()
    discovered=discover(opportunities)
    verified=verify(discovered)
    multi=multichannel(verified)
    leads=acquire_leads(verified)
    sales=autopilot()
    outcomes=process_replies()
    sales_metrics=metrics()
    monitor=check()
    print(json.dumps({"research":"complete","intelligence":intel,"business_discovery":{"businesses":len(discovered)},"contact_verification":{"leads":len(verified),"with_contacts":sum(bool(x.get("channels")) for x in verified)},"multichannel":multi,"lead_acquisition":leads,"sales":sales,"outcomes":outcomes,"sales_metrics":sales_metrics,"monitor":monitor},indent=2))

if __name__=="__main__":main()
