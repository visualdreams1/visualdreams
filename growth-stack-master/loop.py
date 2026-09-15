"""Growth Stack Master execution loop.

Usage:
    python loop.py
    python loop.py research
    python loop.py dashboard

This is the control loop, not an autonomous money-moving system. It can prepare work
and research queues; consequential external actions remain approval-gated.
"""
from __future__ import annotations

import json
import sys
from operator import mission_001, dashboard
from research_loop import daily_loop


def run() -> None:
    mission_001()
    command = sys.argv[1].lower() if len(sys.argv) > 1 else "cycle"

    if command == "research":
        print(json.dumps(daily_loop(), indent=2))
        return

    if command == "dashboard":
        print(dashboard())
        return

    print("GROWTH STACK MASTER — EXECUTION LOOP")
    print("1. CHECK: load mission and pending approvals")
    print("2. RESEARCH: scan the broad opportunity matrix")
    print("3. SCORE: prioritize speed, demand, cost, demo-ability and recurring revenue")
    print("4. PLAN: create the smallest sellable next action")
    print("5. APPROVAL: stop for Dennis when an external/consequential action is required")
    print("6. EXECUTE: perform only approved actions through connected tools")
    print("7. MEASURE: revenue, leads, conversion, delivery and retention")
    print("8. LEARN: record evidence and update priorities")
    print("9. REPEAT: return to research and the highest-value next action")
    print("\nRunning the initial research queue...")
    report = daily_loop()
    print(f"Research matrix: {report['queue_size']} opportunity combinations")
    print(f"Stored candidates: {report['stored_opportunities']}")
    print(f"Income channel: M-Pesa {report['income_number']}")
    print("\nNEXT: connect a live research provider, then validate and rank the best opportunities.")


if __name__ == "__main__":
    run()
