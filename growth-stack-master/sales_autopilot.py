"""Growth Stack sales autopilot.

Creates personalized outreach from evidence-backed opportunities and can hand
messages to an approved sender webhook. External sending is disabled by default.
The sender must enforce consent/opt-out rules and its own authentication.
"""
from __future__ import annotations
import json, os, time, urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
STATE = ROOT / "state"
STATE.mkdir(exist_ok=True)
QUEUE = STATE / "sales_queue.json"
LOG = STATE / "sales_activity.jsonl"

MAX_SENDS_PER_RUN = int(os.getenv("MAX_SALES_SENDS_PER_RUN", "10"))
MIN_SCORE = float(os.getenv("SALES_MIN_SCORE", "70"))
OUTBOUND_ENABLED = os.getenv("OUTBOUND_ENABLED", "0").lower() in {"1", "true", "yes"}
SENDER_WEBHOOK = os.getenv("SALES_SENDER_WEBHOOK", "")


def now():
    return datetime.now(timezone.utc).isoformat()


def load_json(path, default):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else default


def save_json(path, data):
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def make_message(item):
    sector = item.get("sector", "business")
    market = item.get("market", "your market")
    offer = item.get("recommended_offer") or item.get("type", "AI automation")
    return (
        f"Hello! I work with Growth Stack Global, helping {sector} businesses in {market} "
        f"use practical AI to save time and win more customers. We are currently offering "
        f"a simple {offer} solution. If improving customer response, sales follow-up or "
        f"daily operations is a priority, I can show you a quick demo. No obligation. "
        f"Reply YES and I’ll send the details, or STOP if you don’t want further messages."
    )


def build_sales_queue(limit=100):
    opportunities = load_json(STATE / "opportunities.json", [])
    existing = load_json(QUEUE, [])
    seen = {x.get("opportunity_key") for x in existing}
    created = 0
    for item in opportunities:
        if float(item.get("score", 0)) < MIN_SCORE:
            continue
        key = "|".join(str(item.get(k, "")) for k in ("market", "sector", "type"))
        if key in seen:
            continue
        existing.append({
            "opportunity_key": key,
            "market": item.get("market"),
            "sector": item.get("sector"),
            "type": item.get("type"),
            "score": item.get("score", 0),
            "confidence": item.get("confidence", 0),
            "message": make_message(item),
            "status": "READY_FOR_LEAD",
            "created_at": now(),
        })
        seen.add(key); created += 1
        if created >= limit:
            break
    save_json(QUEUE, existing)
    return existing


def send_webhook(payload):
    req = urllib.request.Request(
        SENDER_WEBHOOK,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=20) as response:
        return response.status


def execute(max_sends=MAX_SENDS_PER_RUN):
    queue = load_json(QUEUE, [])
    sent = 0
    for item in queue:
        if sent >= max_sends:
            break
        if item.get("status") != "APPROVED_TO_SEND":
            continue
        if not OUTBOUND_ENABLED or not SENDER_WEBHOOK:
            item["status"] = "APPROVAL_REQUIRED"
            continue
        try:
            status = send_webhook({
                "campaign": "growth-stack-sales",
                "opportunity_key": item["opportunity_key"],
                "message": item["message"],
                "market": item.get("market"),
                "sector": item.get("sector"),
            })
            item["status"] = "SENT" if 200 <= status < 300 else "SEND_FAILED"
            item["sent_at"] = now()
            sent += 1
        except Exception as exc:
            item["status"] = "SEND_FAILED"
            item["error"] = str(exc)[:300]
        with LOG.open("a", encoding="utf-8") as f:
            f.write(json.dumps({"at": now(), "status": item["status"], "key": item["opportunity_key"]}) + "\n")
        time.sleep(float(os.getenv("SALES_SEND_DELAY_SECONDS", "8")))
    save_json(QUEUE, queue)
    return {"outbound_enabled": OUTBOUND_ENABLED, "queued": len(queue), "sent_this_run": sent}


def autopilot():
    build_sales_queue()
    return execute()


if __name__ == "__main__":
    print(json.dumps(autopilot(), indent=2))
