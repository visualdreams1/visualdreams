"""Growth Stack AI evidence processor.

Consumes research snapshots, compares independent evidence, detects material changes,
clusters duplicate opportunities, and writes a ranked owner decision queue.
Optional OpenAI synthesis is enabled with OPENAI_API_KEY. Without it, the engine still
performs deterministic evidence scoring and never invents evidence.
"""
from __future__ import annotations
import json, os, re, urllib.request
from datetime import datetime, timezone
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parent
STATE = ROOT / "state"
STATE.mkdir(exist_ok=True)
OPPS = STATE / "opportunities.json"
QUEUE = STATE / "decision_queue.json"
SNAP = STATE / "opportunity_snapshots.json"
HEALTH = STATE / "intelligence_health.json"
REPORT = ROOT / "DECISION_QUEUE.md"
MODEL = os.getenv("OPENAI_MODEL", "gpt-5.6-luna")


def now(): return datetime.now(timezone.utc).isoformat()
def load(path, default):
    try: return json.loads(path.read_text(encoding="utf-8")) if path.exists() else default
    except Exception: return default
def save(path, obj): path.write_text(json.dumps(obj, indent=2, ensure_ascii=False), encoding="utf-8")

def text(item):
    return " ".join(str(item.get(k,"")) for k in ("market","sector","type","recommended_offer","demand_signal","competition"))

def evidence_quality(e):
    urls = {x.get("url") or x.get("source") for x in e if isinstance(x,dict)} - {None,""}
    domains = {re.sub(r"^www\\.","", re.split(r"/", str(u).split("//")[-1])[0]) for u in urls}
    fresh = sum(1 for x in e if str(x.get("published_at","") or x.get("date","")).strip())
    return min(100, len(domains)*15 + fresh*5 + min(len(e),10)*5)

def deterministic(item):
    ev = item.get("evidence") or []
    domains = set()
    for x in ev:
        u = str(x.get("url") or x.get("source") or "")
        if "//" in u: domains.add(u.split("//",1)[1].split("/",1)[0].lower().removeprefix("www."))
    independent = len(domains)
    q = evidence_quality(ev)
    base = float(item.get("score",0))
    signal = str(item.get("demand_signal","UNKNOWN")).lower()
    demand = 20 if any(w in signal for w in ("high","strong","growing")) else 5 if signal == "unknown" else 10
    score = min(100, round(base*8 + q*.45 + demand, 1))
    confidence = min(0.98, round(.20 + independent*.12 + min(len(ev),8)*.04, 2))
    return score, confidence, independent

def openai_analyze(item):
    key = os.getenv("OPENAI_API_KEY")
    if not key: return None
    payload = {
      "model": MODEL,
      "input": [{"role":"system","content":"You are Growth Stack Global's evidence analyst. Use ONLY supplied evidence. Never invent facts. Return JSON with: verdict, confidence_0_to_1, demand, competition, change, reason, recommended_action."},
                {"role":"user","content":json.dumps(item, ensure_ascii=False)[:30000]}],
      "text":{"format":{"type":"json_object"}}
    }
    req=urllib.request.Request("https://api.openai.com/v1/responses", data=json.dumps(payload).encode(), headers={"Authorization":"Bearer "+key,"Content-Type":"application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            raw=json.loads(r.read().decode())
        out=raw.get("output_text")
        if out: return json.loads(out)
    except Exception: return None
    return None

def change_detection(items, previous):
    old={x.get("key"):x for x in previous}
    changes=[]
    for x in items:
        key=x["key"]; p=old.get(key)
        if not p: changes.append("NEW"); continue
        if x["evidence_count"] > p.get("evidence_count",0): changes.append("NEW_EVIDENCE")
        elif x["score"] >= p.get("score",0)+12: changes.append("STRENGTHENING")
        elif x["score"] <= p.get("score",0)-12: changes.append("WEAKENING")
        else: changes.append("STABLE")
    return changes

def build_queue():
    raw=load(OPPS,[]); previous=load(SNAP,[]); analysed=[]
    clusters=defaultdict(list)
    for item in raw:
        key="|".join(str(item.get(k,"")) for k in ("market","sector","type")).lower()
        score,conf,ind=deterministic(item)
        a={"key":key,"market":item.get("market"),"sector":item.get("sector"),"type":item.get("type"),"evidence":item.get("evidence",[]),"evidence_count":len(item.get("evidence",[])),"independent_sources":ind,"evidence_quality":evidence_quality(item.get("evidence",[])),"score":score,"confidence":conf,"recommended_offer":item.get("recommended_offer","")}
        ai=openai_analyze(a)
        if ai:
            a["ai_analysis"]=ai; a["confidence"]=max(a["confidence"],float(ai.get("confidence_0_to_1",0) or 0))
            if ai.get("recommended_action"): a["recommended_action"]=ai["recommended_action"]
            a["reason"]=ai.get("reason","")
        clusters[(str(a["sector"])+"|"+str(a["type"])).lower()].append(a)
        analysed.append(a)
    changes=change_detection(analysed, previous)
    for a,c in zip(analysed,changes):
        a["change_type"]=c
        if a["score"]>=70 and a["confidence"]>=.65 and a["independent_sources"]>=2: a["status"]="APPROVAL_REQUIRED"
        elif a["score"]>=50: a["status"]="INVESTIGATE"
        elif c in ("NEW","NEW_EVIDENCE","STRENGTHENING"): a["status"]="WATCH"
        else: a["status"]="HOLD"
        a["researched_at"]=now()
    analysed.sort(key=lambda x:(x["score"],x["confidence"],x["independent_sources"]),reverse=True)
    save(QUEUE,analysed[:500]); save(SNAP,analysed[:500])
    write_report(analysed)
    health={"status":"HEALTHY","last_run":now(),"items_analysed":len(analysed),"approval_candidates":sum(x["status"]=="APPROVAL_REQUIRED" for x in analysed),"new_or_changed":sum(x["change_type"]!="STABLE" for x in analysed),"ai_enabled":bool(os.getenv("OPENAI_API_KEY"))}
    save(HEALTH,health)
    return health

def write_report(items):
    lines=["# Growth Stack Global — AI Decision Queue", "", "Generated: "+now(), "", "Automatic research is allowed. Consequential execution still requires Dennis's approval.", ""]
    for i,x in enumerate(items[:30],1):
        lines += [f"## {i}. {x['market']} — {x['sector']} — {x['type']}", f"**Status:** {x['status']}  | **Score:** {x['score']}/100  | **Confidence:** {x['confidence']:.2f}  | **Independent sources:** {x['independent_sources']}", f"**Change:** {x['change_type']}  | **Evidence quality:** {x['evidence_quality']}", f"**Recommended action:** {x.get('recommended_action') or x.get('recommended_offer') or 'Investigate customer demand and willingness to pay.'}", ""]
    REPORT.write_text("\n".join(lines),encoding="utf-8")

if __name__ == "__main__": print(json.dumps(build_queue(),indent=2))
