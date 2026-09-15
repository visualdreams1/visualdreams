"""Growth Stack Master - portable, approval-gated business operator.

V0.1 deliberately uses only Python's standard library. It is a local orchestration
layer: it stores business state, evaluates priorities, creates an execution queue,
and records approvals/results. An LLM or external tools can be plugged in later.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
STATE_DIR = ROOT / "state"
STATE_DIR.mkdir(exist_ok=True)
STATE_FILE = STATE_DIR / "business_state.json"
LOG_FILE = STATE_DIR / "activity.log"

DEFAULT_STATE = {
    "company": "Growth Stack Global",
    "owner": "Dennis",
    "first_customer": "Growth Stack Global",
    "mission": "Get the first real paying AI-services customer with minimum cash outlay.",
    "cash_spend_requires_approval": True,
    "external_send_requires_approval": True,
    "status": "READY",
    "revenue": 0.0,
    "expenses": 0.0,
    "leads": [],
    "customers": [],
    "products": [
        "WhatsApp AI Employee",
        "AI Customer Support",
        "AI Voice Receptionist",
        "AI Sales Agent",
        "AI Business Automation",
        "AI Marketing Machine",
        "AI Research Reports",
        "AI Proposal and Funding Assistant",
        "Custom AI Agent Implementation",
    ],
    "tasks": [],
    "decisions": [],
}


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_state() -> dict[str, Any]:
    if not STATE_FILE.exists():
        save_state(DEFAULT_STATE)
    return json.loads(STATE_FILE.read_text(encoding="utf-8"))


def save_state(state: dict[str, Any]) -> None:
    STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")


def log(event: str, **data: Any) -> None:
    record = {"time": now(), "event": event, **data}
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")


def add_task(title: str, priority: str, reason: str, approval_required: bool = False) -> dict[str, Any]:
    state = load_state()
    task = {
        "id": f"T-{len(state['tasks']) + 1:04d}",
        "title": title,
        "priority": priority,
        "reason": reason,
        "approval_required": approval_required,
        "status": "WAITING_APPROVAL" if approval_required else "READY",
        "created_at": now(),
    }
    state["tasks"].append(task)
    save_state(state)
    log("task_created", task=task)
    return task


def mission_001() -> list[dict[str, Any]]:
    """Create the first execution queue; does not send messages or spend money."""
    state = load_state()
    if state["tasks"]:
        return state["tasks"]
    add_task(
        "Choose one high-demand niche for the first Growth Stack offer",
        "P0",
        "Fast validation beats building a broad platform.",
    )
    add_task(
        "Create one working demonstration of the selected AI service",
        "P0",
        "A demonstrable result is needed for sales.",
    )
    add_task(
        "Build a prospect list of 20 suitable businesses",
        "P0",
        "The first paying customer requires qualified prospects.",
    )
    add_task(
        "Prepare a short sales offer and WhatsApp outreach message",
        "P0",
        "Turn the demonstration into a clear commercial offer.",
        approval_required=True,
    )
    add_task(
        "Prepare a simple customer onboarding checklist",
        "P1",
        "Delivery should be repeatable after the first sale.",
    )
    return load_state()["tasks"]


def dashboard() -> str:
    s = load_state()
    ready = sum(t["status"] == "READY" for t in s["tasks"])
    waiting = sum(t["status"] == "WAITING_APPROVAL" for t in s["tasks"])
    done = sum(t["status"] == "DONE" for t in s["tasks"])
    return f"""\nGROWTH STACK MASTER — CONTROL ROOM\n----------------------------------\nStatus: {s['status']}\nMission: {s['mission']}\nRevenue: {s['revenue']:.2f}\nExpenses: {s['expenses']:.2f}\nLeads: {len(s['leads'])}\nCustomers: {len(s['customers'])}\nTasks: {len(s['tasks'])} | Ready {ready} | Approval {waiting} | Done {done}\n\nNEXT: {next_action(s)}\n"""


def next_action(state: dict[str, Any] | None = None) -> str:
    s = state or load_state()
    priority = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}
    pending = [t for t in s["tasks"] if t["status"] == "READY"]
    if not pending:
        approvals = [t for t in s["tasks"] if t["status"] == "WAITING_APPROVAL"]
        if approvals:
            return f"OWNER APPROVAL: {approvals[0]['title']}"
        return "No ready task. Run mission_001() or add a task."
    return min(pending, key=lambda t: priority.get(t["priority"], 9))["title"]


def approve(task_id: str) -> dict[str, Any]:
    state = load_state()
    for task in state["tasks"]:
        if task["id"] == task_id:
            task["status"] = "READY"
            task["approved_at"] = now()
            state["decisions"].append({"task_id": task_id, "decision": "APPROVED", "time": now()})
            save_state(state)
            log("task_approved", task_id=task_id)
            return task
    raise ValueError(f"Unknown task: {task_id}")


def complete(task_id: str, result: str) -> dict[str, Any]:
    state = load_state()
    for task in state["tasks"]:
        if task["id"] == task_id:
            task["status"] = "DONE"
            task["result"] = result
            task["completed_at"] = now()
            save_state(state)
            log("task_completed", task_id=task_id, result=result)
            return task
    raise ValueError(f"Unknown task: {task_id}")


def add_lead(name: str, category: str, contact: str = "", notes: str = "") -> dict[str, Any]:
    state = load_state()
    lead = {"name": name, "category": category, "contact": contact, "notes": notes, "status": "NEW", "created_at": now()}
    state["leads"].append(lead)
    save_state(state)
    log("lead_added", lead=lead)
    return lead


if __name__ == "__main__":
    mission_001()
    print(dashboard())
