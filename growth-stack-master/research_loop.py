"""Growth Stack opportunity engine with pluggable live research."""
from __future__ import annotations
import json, os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable
ROOT=Path(__file__).resolve().parent; STATE_DIR=ROOT/"state"; STATE_DIR.mkdir(exist_ok=True); OPPORTUNITY_FILE=STATE_DIR/"opportunities.json"; CURSOR_FILE=STATE_DIR/"research_cursor.json"
MPESA_NUMBER="0746352017"
MARKETS=["Mtwapa","Kilifi","Kenya","Tanzania","Uganda","Rwanda","Nigeria","Ghana","South Africa","Egypt","Morocco","UAE","Saudi Arabia","India","Pakistan","Bangladesh","Singapore","Indonesia","Philippines","Japan","South Korea","Australia","New Zealand","UK","Ireland","Germany","France","Netherlands","Nordics","USA","Canada","Mexico","Brazil","Caribbean","Latin America","East Africa","Africa","Global"]
SECTORS=["hotels","restaurants","salons","fashion","real estate","tour operators","schools","NGOs","professional services","shops","events","creative businesses","online businesses","SMEs","health and wellness","property management","logistics","education","hospitality","travel","construction","finance"]
OPPORTUNITY_TYPES=["AI customer support","WhatsApp sales","AI voice receptionist","lead follow-up","business automation","AI marketing system","research-as-a-service","proposal and grant assistance","document processing","appointment booking","review/reputation automation","AI knowledge base","workflow automation","local-language AI","Swahili AI","custom AI agent","AI implementation","AI safety/security","data/reporting automation","micro-SaaS"]
def now():return datetime.now(timezone.utc).isoformat()
def load_opportunities():return json.loads(OPPORTUNITY_FILE.read_text(encoding="utf-8")) if OPPORTUNITY_FILE.exists() else []
def save_opportunities(items):OPPORTUNITY_FILE.write_text(json.dumps(items,indent=2,ensure_ascii=False),encoding="utf-8")
def build_research_queue():return [{"market":m,"sector":s,"type":k} for m in MARKETS for s in SECTORS for k in OPPORTUNITY_TYPES]
def score(item):
 value=0.0;text=f"{item.get('sector','')} {item.get('type','')}".lower()
 if any(x in text for x in ["whatsapp","follow-up","booking","customer support"]):value+=2
 if any(x in text for x in ["automation","agent","voice"]):value+=2
 if item.get("market") in {"Mtwapa","Kilifi","Kenya"}:value+=1
 if item.get("market") in {"Africa","Global"}:value+=1
 if any(x in text for x in ["research","proposal","grant"]):value+=1
 value+=min(len(item.get("evidence",[])),5)*.5
 return round(value,2)
def normalize_research(raw):
 r=dict(raw);r.setdefault("evidence",[]);r.setdefault("demand_signal","UNKNOWN");r.setdefault("competition","UNKNOWN");r.setdefault("startup_cost","UNKNOWN");r.setdefault("recurring_revenue","UNKNOWN");r.setdefault("ease_of_demo","UNKNOWN");r.setdefault("customer_access","UNKNOWN");r.setdefault("recommended_offer","");r["score"]=score(r);r["researched_at"]=now();return r
def _batch(queue,limit):
 if not limit:return queue
 try:cursor=int(json.loads(CURSOR_FILE.read_text(encoding="utf-8")).get("offset",0)) if CURSOR_FILE.exists() else 0
 except Exception:cursor=0
 batch=queue[cursor:cursor+limit]
 if len(batch)<limit:batch+=queue[:limit-len(batch)]
 next_offset=(cursor+limit)%len(queue) if queue else 0
 CURSOR_FILE.write_text(json.dumps({"offset":next_offset,"batch_size":limit,"total":len(queue),"updated_at":now()},indent=2),encoding="utf-8")
 return batch
def run_research(provider:Callable[[dict[str,str]],dict[str,Any]]|None=None,limit:int|None=None):
 queue=build_research_queue(); batch=_batch(queue,limit) if provider else (queue[:limit] if limit else queue); existing=load_opportunities();index={(x.get("market"),x.get("sector"),x.get("type")):i for i,x in enumerate(existing)};processed=[]
 for q in batch:
  key=(q["market"],q["sector"],q["type"]);item=normalize_research(provider(q) if provider else q);processed.append(item)
  if key in index and provider:existing[index[key]]=item
  elif key not in index:index[key]=len(existing);existing.append(item)
 existing.sort(key=lambda x:x.get("score",0),reverse=True);save_opportunities(existing);return processed if provider else existing
def top_opportunities(n=20):return load_opportunities()[:n]
def daily_loop(provider=None,limit=None):
 results=run_research(provider=provider,limit=limit);return {"status":"RESEARCH_COMPLETE" if provider else "RESEARCH_QUEUE_READY","queue_size":len(build_research_queue()),"stored_opportunities":len(load_opportunities()),"processed_this_run":len(results),"top":top_opportunities(10),"income_channel":"M-Pesa","income_number":MPESA_NUMBER}
if __name__=="__main__":print(json.dumps(daily_loop(),indent=2))
