"""Live Tavily research adapter for Growth Stack."""
from __future__ import annotations
import json, os, urllib.request
from typing import Any
from research_loop import run_research
TAVILY_URL="https://api.tavily.com/search"

def web_search(query:dict[str,str])->dict[str,Any]:
 key=os.getenv("TAVILY_API_KEY")
 if not key: raise RuntimeError("TAVILY_API_KEY is not configured")
 q=f"{query['market']} {query['sector']} {query['type']} AI business opportunity demand pricing customers 2026"
 payload={"api_key":key,"query":q,"search_depth":"advanced","topic":"general","max_results":5,"include_answer":True,"include_raw_content":False}
 req=urllib.request.Request(TAVILY_URL,data=json.dumps(payload).encode(),headers={"Content-Type":"application/json","User-Agent":"GrowthStackResearch/1.0"},method="POST")
 with urllib.request.urlopen(req,timeout=60) as response: data=json.loads(response.read().decode("utf-8"))
 evidence=[]
 for r in data.get("results",[]): evidence.append({"title":r.get("title",""),"url":r.get("url",""),"content":r.get("content",""),"score":r.get("score",0),"published_at":r.get("published_date","")})
 return {**query,"evidence":evidence,"provider":"tavily","provider_answer":data.get("answer","")}

def research_worldwide(limit=None): return run_research(provider=web_search,limit=limit)
if __name__=="__main__": print(json.dumps({"researched":len(research_worldwide(25))},indent=2))
