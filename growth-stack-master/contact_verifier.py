"""Normalize and rank public business contact channels."""
from __future__ import annotations
import json,re,urllib.parse
from pathlib import Path
ROOT=Path(__file__).resolve().parent;STATE=ROOT/"state";STATE.mkdir(exist_ok=True)
EMAIL_RE=re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$");PHONE_RE=re.compile(r"^\+?[0-9][0-9 .()\-]{7,20}$")
PRIORITY={"whatsapp":100,"email":95,"phone":85,"linkedin":65,"contact_page":55,"website":40,"social":25}
def normalize_phone(v):return re.sub(r"[^+0-9]","",str(v or ""))
def verify(leads):
    out=[]
    for lead in leads:
        website=lead.get("website","");domain=urllib.parse.urlparse(website).netloc.lower().removeprefix("www.");clean=[]
        for c in lead.get("public_contacts",[]) or []:
            ch=str(c.get("channel","")).lower();v=str(c.get("value","")).strip()
            if ch=="email":
                v=v.lower()
                if not EMAIL_RE.match(v):continue
                score=95 if domain and v.rsplit("@",1)[-1]==domain else 75
            elif ch=="phone":
                v=normalize_phone(v)
                if not PHONE_RE.match(v):continue
                score=85
            elif ch in PRIORITY:
                if ch in {"whatsapp","linkedin","contact_page","website","social"} and not v.startswith(("http://","https://")):continue
                score=PRIORITY[ch]
            else:continue
            clean.append({**c,"channel":ch,"value":v,"verification_score":score})
        clean.sort(key=lambda x:x.get("verification_score",0),reverse=True)
        lead=dict(lead);lead["channels"]=clean;lead["primary_contact"]=clean[0] if clean else None;lead["contact_confidence"]=round(clean[0]["verification_score"]/100,2) if clean else 0;out.append(lead)
    (STATE/"contact_verification.json").write_text(json.dumps({"leads":len(out),"verified_contacts":sum(bool(x.get("channels")) for x in out)},indent=2),encoding="utf-8");return out
