"""Create concise human-review sales responses from classified inbound replies.

This module drafts responses; it never sends them. Sending remains behind the
configured provider and explicit approval gate.
"""
from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parent; STATE=ROOT/"state"; STATE.mkdir(exist_ok=True)
INBOX=STATE/"inbound_replies.jsonl"; CRM=STATE/"lead_crm.json"; OUT=STATE/"response_queue.json"

def now(): return datetime.now(timezone.utc).isoformat()
def load(p,d): return json.loads(p.read_text(encoding="utf-8")) if p.exists() else d
def classify(text):
    t=(text or "").lower()
    if any(x in t for x in ("stop","unsubscribe","remove me","do not contact","don't contact")): return "STOP"
    if any(x in t for x in ("not interested","no thanks","not now")): return "NEGATIVE"
    if any(x in t for x in ("yes","interested","demo","details","pricing","price","call me")): return "POSITIVE"
    return "QUESTION"
def draft(lead,result,text):
    name=lead.get("business_name") or "there"
    if result=="STOP": return ""
    if result=="NEGATIVE": return f"Thanks for letting us know, {name}. We won't follow up further. Wishing you all the best."
    if result=="POSITIVE": return f"Thanks, {name}. Great to hear. I can show you a short Growth Stack Global demo and explain the practical AI solution for your business. What time works for you?"
    return f"Thanks for your message, {name}. I’d be happy to help. Growth Stack Global builds practical AI systems for customer support, sales follow-up and business operations. Tell me what you’d like to automate and I’ll suggest a simple approach."
def run():
    crm=load(CRM,{}); existing=load(OUT,[]); seen={x.get("event_id") for x in existing}; added=0
    if not INBOX.exists(): return {"drafts_added":0,"queue":len(existing)}
    for line in INBOX.read_text(encoding="utf-8").splitlines():
        try:e=json.loads(line)
        except Exception:continue
        eid=str(e.get("event_id") or e.get("id") or "") or f"{e.get('lead_key')}|{e.get('text',e.get('body',''))}|{e.get('timestamp',e.get('at',''))}"
        if eid in seen:continue
        key=e.get("lead_key"); lead=crm.get(key,{})
        result=classify(e.get("text",e.get("body",""))); message=draft(lead,result,e.get("text",e.get("body","")))
        if message:
            existing.append({"event_id":eid,"lead_key":key,"business_name":lead.get("business_name"),"classification":result,"reply":message,"status":"READY_FOR_APPROVAL","created_at":now()});added+=1
        seen.add(eid)
    OUT.write_text(json.dumps(existing,indent=2,ensure_ascii=False),encoding="utf-8");return {"drafts_added":added,"queue":len(existing)}
if __name__=="__main__":print(json.dumps(run(),indent=2))
