"""Safaricom Daraja M-Pesa STK Push adapter.

Secrets are read only from environment variables. No payment is considered
successful until the Daraja callback reports a successful transaction.
"""
from __future__ import annotations
import base64, json, os, urllib.parse, urllib.request
from datetime import datetime
from typing import Any

def configured() -> bool:
    return all(os.getenv(k) for k in (
        "MPESA_CONSUMER_KEY","MPESA_CONSUMER_SECRET","MPESA_SHORTCODE","MPESA_PASSKEY"
    ))

def _base() -> str:
    return os.getenv("MPESA_DARAJA_BASE_URL","https://sandbox.safaricom.co.ke").rstrip("/")

def _token() -> str:
    raw = f"{os.environ['MPESA_CONSUMER_KEY']}:{os.environ['MPESA_CONSUMER_SECRET']}".encode()
    req = urllib.request.Request(
        _base()+"/oauth/v1/generate?grant_type=client_credentials",
        headers={"Authorization":"Basic "+base64.b64encode(raw).decode(),"Accept":"application/json"}
    )
    with urllib.request.urlopen(req,timeout=20) as r:
        return json.loads(r.read().decode())["access_token"]

def stk_push(phone: str, amount: float, account_reference: str) -> dict[str, Any]:
    if not configured():
        return {"ok":False,"status":0,"body":"M-Pesa Daraja is not configured"}
    digits = "".join(ch for ch in phone if ch.isdigit())
    if digits.startswith("0"): digits = "254"+digits[1:]
    if not digits.startswith("254") or len(digits) != 12:
        raise ValueError("Use a valid Kenyan M-Pesa phone number")
    amount = int(round(amount))
    if amount < 1: raise ValueError("Amount must be positive")
    ts = datetime.now().strftime("%Y%m%d%H%M%S")
    password = base64.b64encode((os.environ["MPESA_SHORTCODE"]+os.environ["MPESA_PASSKEY"]+ts).encode()).decode()
    body = {
        "BusinessShortCode": os.environ["MPESA_SHORTCODE"],
        "Password": password,
        "Timestamp": ts,
        "TransactionType": os.getenv("MPESA_TRANSACTION_TYPE","CustomerPayBillOnline"),
        "Amount": amount,
        "PartyA": digits,
        "PartyB": os.environ["MPESA_SHORTCODE"],
        "PhoneNumber": digits,
        "CallBackURL": os.getenv("MPESA_CALLBACK_URL","").strip(),
        "AccountReference": account_reference[-10:] if account_reference else "GROWTHSTACK",
        "TransactionDesc": "Growth Stack payment",
    }
    if not body["CallBackURL"]:
        raise ValueError("MPESA_CALLBACK_URL must be configured")
    req = urllib.request.Request(_base()+"/mpesa/stkpush/v1/processrequest",
        data=json.dumps(body).encode(), headers={
            "Authorization":"Bearer "+_token(),"Content-Type":"application/json"
        }, method="POST")
    try:
        with urllib.request.urlopen(req,timeout=30) as r:
            raw=r.read().decode()
            return {"ok":200<=r.status<300,"status":r.status,"body":json.loads(raw) if raw else {}}
    except Exception as exc:
        return {"ok":False,"status":0,"body":str(exc)[:1000]}

if __name__ == "__main__":
    print(json.dumps({"configured":configured()}))
