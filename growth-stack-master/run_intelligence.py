"""Run research, evidence intelligence, sales queueing, and monitoring."""
from __future__ import annotations
import json
from live_research import research_worldwide
from intelligence_engine import build_queue
from monitor import check
from sales_autopilot import build_sales_queue, execute


def main():
    research = research_worldwide(limit=250)
    intel = build_queue()
    sales_queue = build_sales_queue(limit=100)
    sales = execute()
    monitor = check()
    print(json.dumps({
        "research": {"status": "complete", "stored_opportunities": len(research)},
        "intelligence": intel,
        "sales": sales,
        "sales_queue_size": len(sales_queue),
        "monitor": monitor,
    }, indent=2))


if __name__ == "__main__":
    main()
