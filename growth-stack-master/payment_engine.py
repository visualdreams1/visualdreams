"""M-Pesa payment orchestration for Growth Stack Global.

This module prepares invoices/payment requests and reconciles confirmed
provider callbacks. It never fabricates a payment confirmation and never
moves money without an authorized payment provider transaction.
"""
from __future__ import annotations
import hashlib,json,os
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parent; STATE=ROOT/"state"; STATE.mkdir(exist_ok=True)
ORDERS=STATE/"orders.json"; PAYMENTS=STATE/"payments.jsonl"; METRICS=STATE/"payment_metrics.json"
MPESA_NUMBER=os.getenv("MPESA_NUMBER","0746352017")

def now():return datetime.now(timezone.utc).isoformat()
def load(p,d):return json.loads(p.read_text(encoding="utf-8")) if p.exists() else d
def save(p,d):p.write_text(json.dumps(d,indent=2,ensure_ascii=False),encoding="utf-8")
def order_id(customer,amount,offer):return hashlib.sha256(f"{customer}|{amount}|{offer}".encode()).hexdigest()[:16]
def create_order(customer,amount,offer):
    orders=load(ORDERS,{});oid=order_id(customer,amount,offer);orders[oid]={"order_id":oid,"customer":customer,"amount":float(amount),"offer":offer,"pay_to":"M-Pesa","status":"PAYMENT_REQUIRED","created_at":now()};save(ORDERS,orders);return orders[oid]
def reconcile():
    orders=load(ORDERS,{});confirmed=0;failed=0
    if PAYMENTS.exists():
        for line in PAYMENTS.read_text(encoding="utf-8").splitlines():
            try:e=json.loads(line)
            except Exception:continue
            oid=e.get("order_id");status=str(e.get("status","")).upper()
            if oid not in orders:continue
            if status in {"SUCCESS","COMPLETED","CONFIRMED"}:
                orders[oid]["status"]="PAID";orders[oid]["confirmed_at"]=e.get("at",now());orders[oid]["transaction_id"]=e.get("transaction_id");confirmed+=1
            elif status in {"FAILED","CANCELLED"}:orders[oid]["status"]="PAYMENT_FAILED";failed+=1
    save(ORDERS,orders);m={"orders":len(orders),"paid":sum(x.get("status")=="PAID" for x in orders.values()),"payment_failed":sum(x.get("status")=="PAYMENT_FAILED" for x in orders.values()),"updated_at":now()};save(METRICS,m);return m
if __name__=="__main__":print(json.dumps({"mpesa_destination":"configured","metrics":reconcile()},indent=2))
