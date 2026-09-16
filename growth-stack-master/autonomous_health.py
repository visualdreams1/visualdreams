"""Operational health gate for the Growth Stack autonomous pipeline.

Reports configuration readiness without exposing secret values. It never enables
outbound delivery itself. External delivery requires a legitimate sender and the
explicit OUTBOUND_ENABLED setting.
"""
from __future__ import annotations
import json, os
from pathlib import Path
ROOT=Path(__file__).resolve().parent; STATE=ROOT/"state"; STATE.mkdir(exist_ok=True)

def present(name): return bool(os.getenv(name))
def main():
    providers={
        "tavily":present("TAVILY_API_KEY"),
        "brave":present("BRAVE_SEARCH_API_KEY"),
        "google_cse":present("GOOGLE_CSE_API_KEY") and present("GOOGLE_CSE_ID"),
        "serper":present("SERPER_API_KEY"),
        "openai":present("OPENAI_API_KEY"),
    }
    outbound=present("OUTBOUND_ENABLED") and os.getenv("OUTBOUND_ENABLED","").lower() in {"1","true","yes"}
    sender=present("SALES_SENDER_WEBHOOK")
    health={
        "research_ready": any(providers.values()),
        "providers": providers,
        "multi_provider_search": sum(providers.values())>=2,
        "ai_synthesis_ready":providers["openai"],
        "outbound_configured": outbound and sender,
        "outbound_enabled": outbound,
        "sender_webhook_present": sender,
        "safe_default": not outbound,
        "status":"READY_FOR_AUTONOMOUS_INTERNAL_RUN" if any(providers.values()) else "BLOCKED_MISSING_SEARCH_PROVIDER",
    }
    if outbound and not sender: health["status"]="BLOCKED_MISSING_SENDER"
    (STATE/"autonomous_health.json").write_text(json.dumps(health,indent=2),encoding="utf-8")
    print(json.dumps(health,indent=2))
if __name__=="__main__": main()
