"""Growth Stack sales autopilot.

Builds business-specific outreach from qualified public-contact records.
External sending stays disabled unless a legitimate sender webhook and the
explicit outbound switch are configured. STOP/opt-out handling is preserved.
"""
from __future__ import annotations
import json, os, time, urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parent; STATE=ROOT/"state"; STATE.mkdir(exist_ok=True)
QUEUE=STATE/"sales_queue.json"; LOG=STATE/"sales_activity.jsonl"; CRM=STATE/"lead_crm.json"
MAX_SENDS_PER_RUN=int(os.getenv("MAX_SALES_SENDS_PER_RUN","10")); MIN_SCORE=float(os.getenv("SALES_MIN_SCORE","70"))
OUTBOUND_ENABLED=os.getenv("OUTBOUND_ENABLED","0").lower() in {"1","true","yes"}; SENDER_WEBHOOK=os.getenv("SALES_SENDER_WEBHOOK","")

def now():return datetime.now(timezone.utc).isoformat()
def load(path,default):return json.loads(path.read_text(encoding="utf-8")) if path.exists() else default
def save(path,data):path.write_text(json.dumps(data,indent=2,ensure_ascii=False),encoding="utf-8")

def best_channel(lead):
    priority=["whatsapp","email","phone","linkedin","contact_page","website","social"]
    cs=lead.get("channels",[]) or []
    for p in priority:
        for c in cs:
            if c.get("channel")==p:return c
    return cs[0] if cs else {}

def make_message(lead):
    name=lead.get("business_name") or "there"; sector=lead.get("sector") or "your business"; market=lead.get("market") or "your market"; offer=lead.get("opportunity_type") or "AI automation"; pain=(lead.get("pain_signal") or "").strip().replace("\n"," ")[:180]
    observed=f" I noticed this signal in our research: {pain}" if pain else ""
    return (f"Hello {name} — I’m with Growth Stack Global. We help {sector} businesses in {market} "
            f"use practical AI for customer response, sales follow-up and daily operations. "
            f"I believe a {offer} solution could be useful for your business.{observed} "
            f"I can show you a short demo with no obligation. Reply YES for details, or STOP if you do not want further messages.")

def build_sales_queue(limit=100):
    crm=load(CRM,{}); existing=load(QUEUE,[]); seen={x.get("lead_key") for x in existing}; created=0
    for lead in sorted(crm.values(),key=lambda x:x.get("score",0),reverse=True):
        if float(lead.get("score",0))<MIN_SCORE or lead.get("status") not in {"QUALIFIED","NEW","WATCH"}:continue
        key=lead.get("lead_key")
        if not key or key in seen or not lead.get("channels"):continue
        c=best_channel(lead)
        existing.append({"lead_key":key,"business_name":lead.get("business_name"),"market":lead.get("market"),"sector":lead.get("sector"),"opportunity_type":lead.get("opportunity_type"),"score":lead.get("score",0),"confidence":lead.get("confidence",0),"contact":c,"message":make_message(lead),"status":"READY_FOR_APPROVAL","created_at":now()})
        seen.add(key);created+=1
        if created>=limit:break
    save(QUEUE,existing);return existing

def send_webhook(payload):
    req=urllib.request.Request(SENDER_WEBHOOK,data=json.dumps(payload).encode("utf-8"),headers={"Content-Type":"application/json"},method="POST")
    with urllib.request.urlopen(req,timeout=20) as response:return response.status

def execute(max_sends=MAX_SENDS_PER_RUN):
    queue=load(QUEUE,[]);sent=0
    for item in queue:
        if sent>=max_sends:break
        if item.get("status")!="APPROVED_TO_SEND":continue
        if not OUTBOUND_ENABLED or not SENDER_WEBHOOK:
            item["status"]="APPROVAL_REQUIRED";continue
        try:
            status=send_webhook({"campaign":"growth-stack-sales","lead_key":item["lead_key"],"business_name":item.get("business_name"),"contact":item.get("contact"),"message":item.get("message"),"market":item.get("market"),"sector":item.get("sector")})
            item["status"]="SENT" if 200<=status<300 else "SEND_FAILED";item["sent_at"]=now();sent+=1
        except Exception as exc:item["status"]="SEND_FAILED";item["error"]=str(exc)[:300]
        with LOG.open("a",encoding="utf-8") as f:f.write(json.dumps({"at":now(),"status":item["status"],"lead_key":item["lead_key"],"channel":(item.get("contact") or {}).get("channel")})+"\n")
        time.sleep(float(os.getenv("SALES_SEND_DELAY_SECONDS","8")))
    save(QUEUE,queue);return {"outbound_enabled":OUTBOUND_ENABLED,"queued":len(queue),"sent_this_run":sent}

def autopilot():build_sales_queue();return execute()
if __name__=="__main__":print(json.dumps(autopilot(),indent=2))
