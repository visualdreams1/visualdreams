"""Bounded revenue loop: identify paid orders, trigger fulfillment readiness,
and keep payment follow-up queued without moving funds or sending unapproved
commercial commitments."""
from __future__ import annotations
import json,os
from datetime import datetime,timezone,timedelta
from pathlib import Path
ROOT=Path(__file__).resolve().parent;STATE=ROOT/"state";STATE.mkdir(exist_ok=True)
ORDERS=STATE/"orders.json";QUEUE=STATE/"revenue_actions.json";CRM=STATE/"lead_crm.json"

def now():return datetime.now(timezone.utc).isoformat()
def load(p,d):return json.loads(p.read_text(encoding="utf-8")) if p.exists() else d
def save(p,d):p.write_text(json.dumps(d,indent=2,ensure_ascii=False),encoding="utf-8")
def run():
    orders=load(ORDERS,{});actions=load(QUEUE,[]);seen={x.get("order_id") for x in actions};added=0
    for oid,o in orders.items():
        if oid in seen:continue
        if o.get("status")=="PAID":
            actions.append({"order_id":oid,"type":"FULFILLMENT_READY","customer":o.get("customer"),"offer":o.get("offer"),"status":"READY_FOR_APPROVAL","created_at":now()});added+=1
        elif o.get("status")=="PAYMENT_REQUIRED":
            actions.append({"order_id":oid,"type":"PAYMENT_FOLLOWUP","customer":o.get("customer"),"offer":o.get("offer"),"status":"READY_FOR_APPROVAL","created_at":now()});added+=1
    save(QUEUE,actions);return {"actions_added":added,"queue":len(actions)}
if __name__=="__main__":print(json.dumps(run(),indent=2))
