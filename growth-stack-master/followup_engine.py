"""Reply-aware follow-up scheduler.
No external message is sent here; delivery remains provider-controlled."""
from __future__ import annotations
import json, os
from datetime import datetime, timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parent; STATE=ROOT/"state"; Q=STATE/"followup_queue.json"; CRM=STATE/"lead_crm.json"
MAX=int(os.getenv("MAX_FOLLOWUPS_PER_RUN","20"))

def load(p,d): return json.loads(p.read_text(encoding="utf-8")) if p.exists() else d
def save(p,d): p.write_text(json.dumps(d,indent=2,ensure_ascii=False),encoding="utf-8")
def due(x):
    try:return datetime.fromisoformat(x.get("due_at","").replace("Z","+00:00"))<=datetime.now(timezone.utc)
    except:return False

def run():
    q=load(Q,[]); crm=load(CRM,{}); ready=[]; suppressed=0
    for x in q:
        lead=crm.get(x.get("lead_key"),{})
        state=lead.get("status")
        reply=lead.get("reply_state")
        if state in {"DO_NOT_CONTACT","SUPPRESSED"} or reply in {"STOP","NEGATIVE","BOUNCE"}:
            if x.get("status") not in {"SUPPRESSED","SENT"}: x["status"]="SUPPRESSED"
            suppressed+=1; continue
        if reply in {"POSITIVE","QUESTION"} or state=="ENGAGED":
            x["status"]="ENGAGED"; continue
        if x.get("status") in {"WAITING","READY_FOR_APPROVAL"} and due(x):
            x["status"]="READY_FOR_APPROVAL"; ready.append(x)
            if len(ready)>=MAX: break
    save(Q,q)
    return {"status":"FOLLOWUPS_READY","due_count":len(ready),"approval_required":len(ready),"suppressed":suppressed}
if __name__=="__main__": print(json.dumps(run(),indent=2))
