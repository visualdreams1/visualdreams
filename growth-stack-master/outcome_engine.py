"""Reply classification, opt-out suppression, metrics and bounded learning.

An approved messaging/inbox provider may append inbound replies to
state/inbound_replies.jsonl. This module never sends a reply itself.
Each inbound event should include a stable event_id; a deterministic fallback
is used when a provider does not supply one so repeated polling does not
inflate outcomes.
"""
from __future__ import annotations
import hashlib,json,re
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parent;STATE=ROOT/"state";STATE.mkdir(exist_ok=True)
INBOX=STATE/"inbound_replies.jsonl";CRM=STATE/"lead_crm.json";FOLLOW=STATE/"followup_queue.json";METRICS=STATE/"sales_metrics.json";PROCESSED=STATE/"processed_reply_events.json"
PATTERNS={"STOP":r"\b(stop|unsubscribe|remove me|do not contact|don't contact|no more)\b","POSITIVE":r"\b(yes|interested|demo|tell me more|send details|call me|pricing|price|interested)\b","NEGATIVE":r"\b(no thanks|not interested|not now|no thank you)\b","BOUNCE":r"\b(undeliverable|mailbox unavailable|address not found|bounce)\b"}
def classify(text):
    t=(text or "").lower()
    if re.search(PATTERNS["STOP"],t):return "STOP"
    if re.search(PATTERNS["BOUNCE"],t):return "BOUNCE"
    if re.search(PATTERNS["POSITIVE"],t):return "POSITIVE"
    if re.search(PATTERNS["NEGATIVE"],t):return "NEGATIVE"
    return "QUESTION"
def now():return datetime.now(timezone.utc).isoformat()
def load(p,d):return json.loads(p.read_text(encoding="utf-8")) if p.exists() else d
def save(p,d):p.write_text(json.dumps(d,indent=2,ensure_ascii=False),encoding="utf-8")
def event_id(e):
    raw=str(e.get("event_id") or e.get("id") or "")
    if raw:return raw
    return hashlib.sha256(json.dumps({"lead_key":e.get("lead_key"),"text":e.get("text",e.get("body","")),"at":e.get("at",e.get("timestamp","")),"channel":e.get("channel","")},sort_keys=True).encode()).hexdigest()
def process_replies():
    if not INBOX.exists():return {"processed":0,"skipped_duplicates":0}
    crm=load(CRM,{});q=load(FOLLOW,[]);done=set(load(PROCESSED,[]));processed=0;skipped=0;counts={}
    for line in INBOX.read_text(encoding="utf-8").splitlines():
        try:e=json.loads(line)
        except Exception:continue
        eid=event_id(e)
        if eid in done:skipped+=1;continue
        done.add(eid);key=e.get("lead_key");result=classify(e.get("text",e.get("body","")));counts[result]=counts.get(result,0)+1;processed+=1
        if key in crm:
            crm[key]["last_reply"]={"at":now(),"classification":result,"event_id":eid};crm[key]["reply_state"]=result
            if result=="STOP":crm[key]["status"]="DO_NOT_CONTACT"
            elif result in {"POSITIVE","QUESTION"}:crm[key]["status"]="ENGAGED"
            elif result in {"NEGATIVE","BOUNCE"}:crm[key]["status"]="SUPPRESSED"
        for f in q:
            if f.get("lead_key")==key and result in {"STOP","NEGATIVE","BOUNCE"}:f["status"]="SUPPRESSED"
            elif f.get("lead_key")==key and result in {"POSITIVE","QUESTION"}:f["status"]="ENGAGED"
    save(PROCESSED,sorted(done));save(CRM,crm);save(FOLLOW,q)
    previous=load(METRICS,{})
    cumulative=previous.get("reply_counts",{})
    for k,v in counts.items():cumulative[k]=int(cumulative.get(k,0))+v
    save(METRICS,{**previous,"last_reply_processing_at":now(),"last_run_reply_counts":counts,"reply_counts":cumulative})
    return {"processed":processed,"skipped_duplicates":skipped,"counts":counts}
def metrics():
    crm=load(CRM,{});q=load(STATE/"sales_queue.json",[]);sent=sum(1 for x in q if x.get("status")=="SENT");engaged=sum(1 for x in crm.values() if x.get("reply_state") in {"POSITIVE","QUESTION"});optouts=sum(1 for x in crm.values() if x.get("status")=="DO_NOT_CONTACT");m={"leads":len(crm),"sent":sent,"engaged":engaged,"opt_outs":optouts,"reply_rate":round(engaged/sent,3) if sent else 0,"updated_at":now()};save(METRICS,m);return m
if __name__=="__main__":print(json.dumps({"replies":process_replies(),"metrics":metrics()},indent=2))
