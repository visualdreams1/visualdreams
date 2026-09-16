"""Bounded learning loop for Growth Stack Global.

The agent may improve ranking weights from observed outcomes, but it cannot
remove approval gates, increase external-action limits, or authorize spending.
"""
from __future__ import annotations
import json, os
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
STATE = ROOT / "state"
STATE.mkdir(exist_ok=True)
POLICY = STATE / "operator_policy.json"
METRICS = STATE / "adaptive_strategy.json"

DEFAULT = {
    "max_send_per_run": int(os.getenv("MAX_SALES_SENDS_PER_RUN", "10")),
    "max_leads_per_run": int(os.getenv("MAX_LEADS_PER_RUN", "50")),
    "max_followups_per_run": int(os.getenv("MAX_FOLLOWUPS_PER_RUN", "20")),
    "approval_required_for": [
        "external_outreach", "payment_request", "refund", "money_movement",
        "contract", "legal_commitment", "sensitive_publication"
    ],
    "weights": {"reply": 1.0, "positive": 2.5, "paid": 5.0, "repeat": 7.0, "bounce": -2.0, "negative": -1.5},
    "updated_at": None,
}

def load(path, default):
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            pass
    return default.copy() if isinstance(default, dict) else default

def save(path, data):
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

def run():
    policy = load(POLICY, DEFAULT)
    metrics = load(METRICS, {"cycles": 0, "events": {}})
    outcome_path = STATE / "sales_metrics.json"
    outcome = load(outcome_path, {})
    events = metrics.setdefault("events", {})
    for key in ("replies", "positive", "negative", "bounces", "paid", "repeat"):
        if key in outcome:
            events[key] = int(outcome.get(key) or 0)
    # Conservative adaptation: weights move at most 10% per cycle and only
    # ranking/selection changes are allowed. Safety and action limits remain fixed.
    paid = events.get("paid", 0)
    positive = events.get("positive", 0)
    if paid > 0:
        policy["weights"]["paid"] = min(10.0, policy["weights"].get("paid", 5.0) * 1.05)
    if positive > 0:
        policy["weights"]["positive"] = min(6.0, policy["weights"].get("positive", 2.5) * 1.03)
    policy["updated_at"] = datetime.now(timezone.utc).isoformat()
    metrics["cycles"] = int(metrics.get("cycles", 0)) + 1
    metrics["last_cycle_at"] = policy["updated_at"]
    save(POLICY, policy)
    save(METRICS, metrics)
    return {"status": "ADAPTIVE_POLICY_UPDATED", "cycles": metrics["cycles"], "weights": policy["weights"]}

if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
