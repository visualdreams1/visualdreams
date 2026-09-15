"""Multi-channel intelligence layer for Growth Stack.

Normalizes permitted public business signals from multiple research channels,
deduplicates them, scores channel reliability, preserves history, and creates
follow-up plans. This module does not send messages or bypass access controls.
"""
from __future__ import annotations
import json, os, re, hashlib
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT=Path(__file__).resolve().parent; STATE=ROOT/"state"; STATE.mkdir(exist_ok=True)
CRM=STATE/"lead_crm.json"; HISTORY=STATE/"lead_history.jsonl"; FOLLOWUPS=STATE/"followup_queue.json"
MAX=int(os.getenv("MAX_MULTICHANNEL_LEADS","200"))
CHANNEL_WEIGHT={"website":20,"email":18,"phone":15,"whatsapp":18,"linkedin":12,"contact_page":15,"directory":10,"social":8}

def now(): return datetime.now(timezone.utc)
def iso(): return now().isoformat()
def load(p,d): return json.loads(p.read_text(encoding="utf-8")) if p.exists() else d
def save(p,d): p.write_text(json.dumps(d,indent=2,ensure_ascii=False),encoding="utf-8")
def norm(v): return re.sub(r"[^a-z0-9]+"," ",str(v or "").lower()).strip()
def key(x):
    raw="|".join([norm(x.get("business_name")),norm(x.get("market")),norm(x.get("website"))])
    return hashlib.sha256(raw.encode()).hexdigest()[:20]

def extract_channels(item):
    out=[]
    for c in item.get("public_contacts",[]) or []:
        if not isinstance(c,dict): continue
        ch=str(c.get("channel","")).lower(); value=str(c.get("value","")).strip()
        if ch in CHANNEL_WEIGHT and value:
            out.append({"channel":ch,"value":value,"source_url":c.get("source_url","")})
    # Research evidence is a source signal, not a contact. Preserve its URL for provenance.
    sources=[]
    for e in item.get("evidence",[]) or []:
        if isinstance(e,dict) and e.get("url"): sources.append(e["url"])
    return out, sorted(set(sources))

def score(item,channels,sources):
    s=float(item.get("lead_score",item.get("score",0)) or 0)
    s += min(sum(CHANNEL_WEIGHT.get(c["channel"],0) for c in channels),25)
    s += min(len(set(sources))*2,10)
    if item.get("verified_business"): s += 10
    if item.get("pain_signal"): s += 5
    return round(min(100,s),2)

def ingest(items):
    crm=load(CRM,{}); changed=0
    for item in items:
        if not item.get("business_name"): continue
        channels,sources=extract_channels(item)
        if not channels: continue
        k=key(item); old=crm.get(k,{})
        lead=dict(old); lead.update({
            "lead_key":k,"business_name":item.get("business_name"),"market":item.get("market"),
            "sector":item.get("sector"),"website":item.get("website"),"channels":channels,
            "source_urls":sorted(set(old.get("source_urls",[]))|set(sources)),
            "pain_signal":item.get("pain_signal",old.get("pain_signal","")),
            "opportunity_type":item.get("type",item.get("opportunity_type",old.get("opportunity_type",""))),
            "score":score(item,channels,sources),"last_seen":iso(),
            "status":old.get("status","NEW")
        })
        if lead["score"]>=75 and lead["status"] in {"NEW","WATCH"}: lead["status"]="QUALIFIED"
        crm[k]=lead; changed+=1
        with HISTORY.open("a",encoding="utf-8") as f: f.write(json.dumps({"at":iso(),"event":"UPSERT","lead_key":k,"channels":[c["channel"] for c in channels],"score":lead["score"]})+"\n")
    ranked=sorted(crm.values(),key=lambda x:x.get("score",0),reverse=True)
    save(CRM,{x["lead_key"]:x for x in ranked[:MAX]})
    return ranked[:MAX],changed

def build_followups(leads):
    q=load(FOLLOWUPS,[]); existing={(x.get("lead_key"),x.get("step")) for x in q}
    for lead in leads:
        if lead.get("status")!="QUALIFIED": continue
        for step,days in ((1,0),(2,3),(3,7),(4,14)):
            marker=(lead["lead_key"],step)
            if marker in existing: continue
            q.append({"lead_key":lead["lead_key"],"business_name":lead["business_name"],"step":step,"due_at":(now()+timedelta(days=days)).isoformat(),"status":"READY_FOR_APPROVAL" if step==1 else "WAITING","channel_priority":[c["channel"] for c in lead.get("channels",[])],"created_at":iso()})
            existing.add(marker)
    save(FOLLOWUPS,q); return q

def run(items):
    leads,changed=ingest(items); followups=build_followups(leads)
    return {"status":"MULTICHANNEL_INTELLIGENCE_COMPLETE","leads_processed":changed,"crm_leads":len(leads),"followups":len(followups)}
