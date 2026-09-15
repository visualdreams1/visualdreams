"""Growth Stack Master execution loop."""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def load_operator():
    spec = importlib.util.spec_from_file_location("growth_stack_operator", ROOT / "operator.py")
    if spec is None or spec.loader is None:
        raise RuntimeError("Cannot load local operator.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run() -> None:
    operator = load_operator()
    from research_loop import daily_loop

    operator.mission_001()
    command = sys.argv[1].lower() if len(sys.argv) > 1 else "cycle"

    if command == "research":
        print(json.dumps(daily_loop(), indent=2))
        return
    if command == "dashboard":
        print(operator.dashboard())
        return

    print("GROWTH STACK MASTER — EXECUTION LOOP")
    print("CHECK → RESEARCH → SCORE → PLAN → APPROVAL → EXECUTE → MEASURE → LEARN → REPEAT")
    report = daily_loop()
    print(f"Research matrix: {report['queue_size']} opportunity combinations")
    print(f"Stored candidates: {report['stored_opportunities']}")
    print(f"Income channel: M-Pesa {report['income_number']}")
    print("NEXT: run the scheduled live research workflow and review the monitoring dashboard.")


if __name__ == "__main__":
    run()
