"""Business discovery + public contact extraction for Growth Stack.

Uses configured search APIs and public webpages only. It never logs in, bypasses
CAPTCHAs/access controls, guesses contacts, or sends outreach.
"""
from __future__ import annotations
import html, json, os, re, time, urllib.parse, urllib.request
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

ROOT=Path(__file__).resolve().parent; STATE=ROOT/"state"; STATE.mkdir(exist_ok=True)
UA=os.getenv("DISCOVERY_USER_AGENT","GrowthStackDiscovery/1.0 (+public-business-research)")
TIMEOUT=int(os.getenv("DISCOVERY_HTTP_TIMEOUT","15")); MAX_RESULTS=int(os.getenv("DISCOVERY_RESULTS_PER_QUERY","20")); MAX_PAGES=int(os.getenv("DISCOVERY_MAX_PAGES_PER_QUERY","8")); DELAY=float(os.getenv("DISCOVERY_DELAY_SECONDS","0.5"))
EMAIL_RE=re.compile(r"[A-Z0-9._%+\-]+@[A-Z0-9.\-]+\.[A-Z]{2,}",re.I)
PHONE_RE=re.compile(r"(?<!\w)(?:\+?\d[\d .()\-]{7,}\d)(?!\w)")
SOCIAL={"linkedin.com":"linkedin","facebook.com":"social","instagram.com":"social","x.com":"social","twitter.com":"social"}
COUNTRIES={"kenya":"KE","tanzania":"TZ","uganda":"UG","rwanda":"RW","nigeria":"NG","ghana":"GH","south africa":"ZA","egypt":"EG","morocco":"MA","uae":"AE","saudi arabia":"SA","india":"IN","pakistan":"PK","bangladesh":"BD","singapore":"SG","indonesia":"ID","philippines":"PH","japan":"JP","south korea":"KR","australia":"AU","new zealand":"NZ","uk":"GB","ireland":"IE","germany":"DE","france":"FR","netherlands":"NL","usa":"US","canada":"CA","mexico":"MX","brazil":"BR"}

def _get(url,headers=None):
    req=urllib.request.Request(url,headers={"User-Agent":UA,**(headers or {})})
    with urllib.request.urlopen(req,timeout=TIMEOUT) as r: return json.loads(r.read().decode("utf-8",errors="replace"))
def _post(url,payload,headers=None):
    req=urllib.request.Request(url,data=json.dumps(payload).encode(),headers={"Content-Type":"application/json","User-Agent":UA,**(headers or {})},method="POST")
    with urllib.request.urlopen(req,timeout=TIMEOUT) as r: return json.loads(r.read().decode("utf-8",errors="replace"))

def brave_web(q,country="US"):
    key=os.getenv("BRAVE_SEARCH_API_KEY")
    if not key:return []
    p=urllib.parse.urlencode({"q":q,"count":min(MAX_RESULTS,20),"country":country or "US","search_lang":"en","safesearch":"moderate"})
    d=_get("https://api.search.brave.com/res/v1/web/search?"+p,{"X-Subscription-Token":key})
    return [{"provider":"brave_web","title":r.get("title",""),"url":r.get("url",""),"content":r.get("description","")} for r in d.get("web",{}).get("results",[])]

def brave_places(q,location="",country=""):
    key=os.getenv("BRAVE_SEARCH_API_KEY")
    if not key:return []
    p={"q":q,"count":min(MAX_RESULTS,100)}
    if location:p["location"]=location.replace(","," ")
    if country:p["country"]=country
    d=_get("https://api.search.brave.com/res/v1/local/place_search?"+urllib.parse.urlencode(p),{"X-Subscription-Token":key}); out=[]
    for r in d.get("results",[]) or []:
        c=r.get("contact") or {}; out.append({"provider":"brave_places","title":r.get("title",""),"url":r.get("url","") or r.get("provider_url",""),"description":r.get("description",""),"address":(r.get("postal_address") or {}).get("displayAddress",""),"phone":c.get("telephone",""),"email":c.get("email",""),"profiles":r.get("profiles",[]) or []})
    return out

def google_cse(q,country=""):
    key,cx=os.getenv("GOOGLE_CSE_API_KEY"),os.getenv("GOOGLE_CSE_ID")
    if not key or not cx:return []
    p={"key":key,"cx":cx,"q":q,"num":min(MAX_RESULTS,10)}
    if country:p["gl"]=country.lower()
    d=_get("https://www.googleapis.com/customsearch/v1?"+urllib.parse.urlencode(p))
    return [{"provider":"google_cse","title":r.get("title",""),"url":r.get("link",""),"content":r.get("snippet","")} for r in d.get("items",[])]

def serper(q,country=""):
    key=os.getenv("SERPER_API_KEY")
    if not key:return []
    d=_post("https://google.serper.dev/search",{"q":q,"gl":country.lower() if country else None,"num":min(MAX_RESULTS,20)},{"X-API-KEY":key}); return [{"provider":"serper","title":r.get("title",""),"url":r.get("link",""),"content":r.get("snippet","")} for r in d.get("organic",[]) or []]

class Parser(HTMLParser):
    def __init__(self): super().__init__(); self.title=[]; self.text=[]; self.links=[]; self.jsonld=[]; self.tag=""; self.script=None
    def handle_starttag(self,t,a):
        self.tag=t; attrs=dict(a)
        if t=="a" and attrs.get("href"): self.links.append(attrs["href"])
        if t=="script" and attrs.get("type","").lower().startswith("application/ld+json"): self.script=""
    def handle_data(self,d):
        if self.tag=="title":self.title.append(d)
        if self.tag in {"body","main","article","p","div","span","footer","header"}:self.text.append(d)
        if self.tag=="script" and self.script is not None:self.script+=d
    def handle_endtag(self,t):
        if t=="script" and self.script:
            try:self.jsonld.append(json.loads(self.script))
            except Exception:pass
            self.script=None
        self.tag=""

def safe_url(url):
    try:
        p=urllib.parse.urlparse(url); return p.scheme in {"http","https"} and bool(p.netloc)
    except Exception:return False

def fetch_page(url):
    if not safe_url(url):return {}
    try:
        req=urllib.request.Request(url,headers={"User-Agent":UA,"Accept":"text/html,application/xhtml+xml"})
        with urllib.request.urlopen(req,timeout=TIMEOUT) as r:
            final=r.geturl(); ctype=r.headers.get("Content-Type","")
            if "text/html" not in ctype:return {"url":final}
            raw=r.read(700000).decode("utf-8",errors="replace")
        p=Parser();p.feed(raw); links=[urllib.parse.urljoin(final,html.unescape(x)) for x in p.links]
        return {"url":final,"title":" ".join(p.title).strip(),"text":" ".join(" ".join(p.text).split())[:30000],"links":links,"jsonld":p.jsonld}
    except Exception:return {}

def schema_business(data):
    types={"LocalBusiness","Organization","Corporation","Store","Restaurant","Hotel","ProfessionalService","MedicalBusiness","FinancialService"}
    for x in data:
        vals=x if isinstance(x,list) else [x]
        for o in vals:
            if isinstance(o,dict):
                ts=o.get("@type",[]);ts=ts if isinstance(ts,list) else [ts]
                if any(t in types for t in ts):return o
    return {}

def extract_contacts(page,fallback=None):
    fallback=fallback or {}; url=page.get("url",""); schema=schema_business(page.get("jsonld",[])); name=str(schema.get("name") or fallback.get("title") or page.get("title") or "").strip(); out=[]
    def add(ch,val,confidence="observed"):
        val=str(val or "").strip()
        if val:out.append({"channel":ch,"value":val,"source_url":url,"confidence":confidence})
    if fallback.get("email"):add("email",fallback["email"],"provider_verified")
    if fallback.get("phone"):add("phone",fallback["phone"],"provider_verified")
    for e in sorted(set(EMAIL_RE.findall(page.get("text","")+" "+json.dumps(schema))))[:10]:add("email",e)
    phones=[]
    if schema.get("telephone"):phones.append(schema["telephone"])
    phones+=PHONE_RE.findall(page.get("text",""))[:10]
    for p in dict.fromkeys(phones):add("phone",p)
    for link in page.get("links",[]):
        low=link.lower(); host=urllib.parse.urlparse(low).netloc
        if low.startswith("mailto:"):add("email",urllib.parse.unquote(link[7:]).split("?")[0])
        elif low.startswith("tel:"):add("phone",urllib.parse.unquote(link[4:]))
        elif "wa.me/" in low or "whatsapp.com/" in low:add("whatsapp",link,"explicit_public_whatsapp")
        else:
            for dom,ch in SOCIAL.items():
                if dom in host:add(ch,link)
        path=urllib.parse.urlparse(low).path
        if any(x in path for x in ("contact","get-in-touch","reach-us","connect")):add("contact_page",link,"public_contact_page")
    for p in fallback.get("profiles",[]) or []:
        if isinstance(p,dict) and p.get("url"):add("linkedin" if "linkedin" in p["url"].lower() else "social",p["url"],"provider_profile")
    seen=set();clean=[]
    for c in out:
        k=(c["channel"],c["value"])
        if k not in seen:seen.add(k);clean.append(c)
    return name,clean,schema

def discover(opportunities):
    records=[]; fetched=0; seen_urls=set()
    for item in opportunities:
        market=str(item.get("market","")); country=COUNTRIES.get(market.lower(),""); q=f'"{item.get("sector","")}" "{market}" businesses {item.get("type","")} company contact'; results=[]
        for fn,args in ((brave_web,(q,country)),(google_cse,(q,country)),(serper,(q,country))):
            try:results+=fn(*args)
            except Exception:pass
        for e in item.get("evidence",[]) or []:
            if isinstance(e,dict) and e.get("url"):results.append({"provider":"tavily","title":e.get("title",""),"url":e.get("url",""),"content":e.get("content","")})
        try:results+=brave_places(f'{item.get("sector","")} {item.get("type","")}',market,country)
        except Exception:pass
        for r in results:
            url=r.get("url","")
            if not url and not r.get("title"):continue
            direct=[]
            if r.get("phone"):direct.append({"channel":"phone","value":r["phone"],"source_url":url,"confidence":"provider_verified"})
            if r.get("email"):direct.append({"channel":"email","value":r["email"],"source_url":url,"confidence":"provider_verified"})
            for p in r.get("profiles",[]) or []:
                if isinstance(p,dict) and p.get("url"):direct.append({"channel":"linkedin" if "linkedin" in p["url"].lower() else "social","value":p["url"],"source_url":url,"confidence":"provider_profile"})
            if direct and r.get("title"):
                records.append({**item,"business_name":r["title"],"website":url,"public_contacts":direct,"verified_business":True,"discovery_source":r.get("provider"),"discovery_evidence":[r]})
            if safe_url(url) and url not in seen_urls and fetched<MAX_PAGES:
                seen_urls.add(url);fetched+=1;page=fetch_page(url)
                if page:
                    name,contacts,schema=extract_contacts(page,r)
                    if name and contacts:records.append({**item,"business_name":name,"website":page.get("url",url),"public_contacts":contacts,"verified_business":bool(schema),"pain_signal":str(r.get("content","") or "")[:500],"discovery_source":r.get("provider"),"discovery_evidence":[{"provider":r.get("provider"),"url":url,"title":r.get("title","")}]})
                if DELAY:time.sleep(DELAY)
    merged={}
    for x in records:
        domain=urllib.parse.urlparse(x.get("website","")).netloc.lower().removeprefix("www.");k=re.sub(r"[^a-z0-9]","",x.get("business_name","").lower())+"|"+domain
        if k not in merged:merged[k]=dict(x)
        else:
            old=merged[k]; cs={ (c["channel"],c["value"]):c for c in old.get("public_contacts",[])+x.get("public_contacts",[]) };old["public_contacts"]=list(cs.values());old["discovery_evidence"]=(old.get("discovery_evidence",[])+x.get("discovery_evidence",[]))[-10:];old["verified_business"]=old.get("verified_business") or x.get("verified_business")
    out=list(merged.values());(STATE/"discovery_health.json").write_text(json.dumps({"businesses_discovered":len(out),"pages_fetched":fetched,"providers_enabled":[p for p,v in (("tavily",True),("brave",bool(os.getenv("BRAVE_SEARCH_API_KEY"))),("google_cse",bool(os.getenv("GOOGLE_CSE_API_KEY") and os.getenv("GOOGLE_CSE_ID"))),("serper",bool(os.getenv("SERPER_API_KEY")))) if v]},indent=2),encoding="utf-8");return out

if __name__=="__main__":print(json.dumps({"status":"READY","providers":["tavily","brave","google_cse","serper"]},indent=2))
