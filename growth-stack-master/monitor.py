"""Health and execution monitor for Growth Stack Master."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
STATE = ROOT / "state"
OPPS = STATE / "opportunities.json"
HEALTH = STATE / "health.json"


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def check() -> dict:
    errors = []
    warnings = []
    if not OPPS.exists(): warnings.append("No opportunity database yet")
    try:
        count = len(json.loads(OPPS.read_text(encoding="utf-8"))) if OPPS.exists() else 0
    except Exception as exc:
        count = 0
        errors.append(f"Opportunity database unreadable: {exc}")
    status = "HEALTHY" if not errors else "DEGRADED"
    report = {
        "timestamp": utcnow(),
        "status": status,
        "opportunities": count,
        "errors": errors,
        "warnings": warnings,
        "checks": {
            "research_store": OPPS.exists(),
            "state_directory": STATE.exists(),
            "monitor_running": True,
        },
    }
    STATE.mkdir(exist_ok=True)
    HEALTH.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


if __name__ == "__main__":
    print(json.dumps(check(), indent=2))
