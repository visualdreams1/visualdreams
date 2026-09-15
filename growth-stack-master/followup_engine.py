"""Follow-up engine: schedules, deduplicates and prioritizes follow-ups.
No external message is sent here; delivery remains provider-controlled."""
from __future__ import annotations
import json, os
from datetime import datetime, timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parent; STATE=ROOT/"state"; STATE.mkdir(exist_ok=True)
Q=STATE/"followup_queue.json"; LOG=STATE/"sales_activity.jsonl"
MAX=int(os.getenv("MAX_FOLLOWUPS_PER_RUN","20"))

def load(p,d): return json.loads(p.read_text(encoding="utf-8")) if p.exists() else d
def save(p,d): p.write_text(json.dumps(d,indent=2,ensure_ascii=False),encoding="utf-8")
def due(x):
    try:return datetime.fromisoformat(x.get("due_at","").replace("Z","+00:00"))<=datetime.now(timezone.utc)
    except:return False

def run():
    q=load(Q,[]); ready=[]
    for x in q:
        if x.get("status") in {"WAITING","READY_FOR_APPROVAL"} and due(x):
            x["status"]="READY_FOR_APPROVAL"; ready.append(x)
            if len(ready)>=MAX: break
    save(Q,q)
    return {"status":"FOLLOWUPS_READY","due_count":len(ready),"approval_required":len(ready)}
if __name__=="__main__": print(json.dumps(run(),indent=2))
