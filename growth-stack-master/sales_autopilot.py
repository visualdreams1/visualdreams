"""Growth Stack sales autopilot.

Builds business-specific outreach from qualified public-contact records.
External sending stays disabled unless the explicit outbound switch and a
legitimate sender are configured. STOP/opt-out handling is preserved.
WhatsApp can use the official Meta Cloud API directly; other channels can use
the existing sender webhook.
"""
from __future__ import annotations
import hashlib, json, os, time, urllib.error, urllib.request
from datetime import datetime, timezone
from pathlib import Path
from whatsapp_cloud import send as whatsapp_send, configured as whatsapp_configured

ROOT=Path(__file__).resolve().parent; STATE=ROOT/"state"; STATE.mkdir(exist_ok=True)
QUEUE=STATE/"sales_queue.json"; LOG=STATE/"sales_activity.jsonl"; CRM=STATE/"lead_crm.json"
MAX_SENDS_PER_RUN=int(os.getenv("MAX_SALES_SENDS_PER_RUN","10")); MIN_SCORE=float(os.getenv("SALES_MIN_SCORE","70"))
OUTBOUND_ENABLED=os.getenv("OUTBOUND_ENABLED","0").lower() in {"1","true","yes"}; SENDER_WEBHOOK=os.getenv("SALES_SENDER_WEBHOOK","")
RETRIES=int(os.getenv("SALES_SEND_RETRIES","3")); RETRY_DELAY=float(os.getenv("SALES_RETRY_DELAY_SECONDS","3"))


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
        existing.append({"lead_key":key,"business_name":lead.get("business_name"),"market":lead.get("market"),"sector":lead.get("sector"),"opportunity_type":lead.get("opportunity_type"),"score":lead.get("score",0),"confidence":lead.get("confidence",0),"contact":c,"channels":lead.get("channels",[]),"message":make_message(lead),"status":"READY_FOR_APPROVAL","created_at":now()})
        seen.add(key);created+=1
        if created>=limit:break
    save(QUEUE,existing);return existing

def send_webhook(payload, idem_key):
    req=urllib.request.Request(SENDER_WEBHOOK,data=json.dumps(payload).encode("utf-8"),headers={"Content-Type":"application/json","Idempotency-Key":idem_key,"X-Growth-Stack-Campaign":"growth-stack-sales"},method="POST")
    with urllib.request.urlopen(req,timeout=20) as response:return response.status

def send_item(item, idem):
    channel=(item.get("contact") or {}).get("channel")
    value=str((item.get("contact") or {}).get("value") or "")
    if channel=="whatsapp" and whatsapp_configured():
        params=[item.get("business_name") or "business"]
        return whatsapp_send(value,item.get("message", ""),params)
    if SENDER_WEBHOOK:
        payload={"campaign":"growth-stack-sales","lead_key":item["lead_key"],"business_name":item.get("business_name"),"contact":item.get("contact"),"message":item.get("message"),"market":item.get("market"),"sector":item.get("sector")}
        status=send_webhook(payload,idem)
        return {"ok":200<=status<300,"status":status,"body":{}}
    return {"ok":False,"status":0,"body":"No sender configured for selected channel"}

def execute(max_sends=MAX_SENDS_PER_RUN):
    queue=load(QUEUE,[]);crm=load(CRM,{});sent=0;accepted=0
    for item in queue:
        if sent>=max_sends:break
        if item.get("status")!="APPROVED_TO_SEND":continue
        lead=crm.get(item.get("lead_key"),{})
        if lead.get("status") in {"DO_NOT_CONTACT","SUPPRESSED"} or lead.get("reply_state") in {"STOP","NEGATIVE","BOUNCE"}:
            item["status"]="SUPPRESSED";continue
        if not OUTBOUND_ENABLED:
            item["status"]="BLOCKED_OUTBOUND";continue
        idem=hashlib.sha256(f"{item['lead_key']}|{item.get('contact',{}).get('value')}|{item.get('message')}".encode()).hexdigest()
        if item.get("idempotency_key")==idem and item.get("status")=="SENT":continue
        last_error=""
        for attempt in range(1,RETRIES+1):
            try:
                result=send_item(item,idem)
                if result.get("ok"):
                    item["status"]="SENT";item["send_accepted_at"]=now();item["sent_at"]=item.get("sent_at") or item["send_accepted_at"];item["idempotency_key"]=idem;item["send_attempts"]=attempt;accepted+=1;break
                last_error=f"HTTP {result.get('status',0)}: {str(result.get('body',''))[:300]}"
            except (urllib.error.URLError,TimeoutError,Exception) as exc:last_error=str(exc)[:300]
            if attempt<RETRIES:time.sleep(RETRY_DELAY*attempt)
        else:
            item["status"]="SEND_FAILED";item["error"]=last_error;item["send_attempts"]=RETRIES
        sent+=1
        with LOG.open("a",encoding="utf-8") as f:f.write(json.dumps({"at":now(),"status":item["status"],"lead_key":item["lead_key"],"channel":(item.get("contact") or {}).get("channel"),"attempts":item.get("send_attempts",0)})+"\n")
        time.sleep(float(os.getenv("SALES_SEND_DELAY_SECONDS","8")))
    save(QUEUE,queue);return {"outbound_enabled":OUTBOUND_ENABLED,"whatsapp_configured":whatsapp_configured(),"queued":len(queue),"attempted_this_run":sent,"accepted_this_run":accepted}

def autopilot():build_sales_queue();return execute()
if __name__=="__main__":print(json.dumps(autopilot(),indent=2))
