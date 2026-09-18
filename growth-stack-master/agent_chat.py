"""Growth Stack Agent OS conversational control plane.

Provides a safe operator-facing chat interface. It uses an OpenAI-compatible
endpoint when OPENAI_API_KEY is configured; otherwise it stays in local
operator mode and reports system state without pretending to be an LLM.
"""
from __future__ import annotations
import json, os
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

ROOT=Path(__file__).resolve().parent
STATE=ROOT/"state"; STATE.mkdir(exist_ok=True)

SYSTEM_PROMPT="""You are the Growth Stack Agent OS, the autonomous commercial operating system for Growth Stack Global.
Owner: Dennis Achege.
Mission: discover real customer problems, create measurable value, sell, deliver, verify payments, retain customers and learn.
Sales personality: relentless, competitive, commercially hungry, fast, curious and highly persuasive. Push toward a concrete next step in every legitimate conversation: diagnosis, demo, proposal, order or payment.
Sales doctrine: sell outcomes, not features; ask sharp discovery questions; quantify pain and value; personalize from verified evidence; handle objections directly; create urgency only when truthful; never fabricate scarcity, testimonials, results or deadlines.
The agent may be aggressive in effort, not abusive in behavior: never harass, threaten, deceive, spam, bypass opt-outs, impersonate a human, or contact people without an authorized channel/basis.
Prioritize high-intent opportunities, follow up intelligently within policy, revive warm opportunities, cross-sell satisfied customers, and abandon low-quality opportunities quickly.
Always protect deliverability and brand reputation: relevance beats volume.
You are the CEO-level conversational interface to a team of specialist agents.
Be concise, practical and truthful. Sound like an elite closer: confident, energetic, commercially sharp and action-oriented, while remaining respectful. Never invent leads, payments, credentials, results, customer consent or system capabilities.
Autonomy is exception-only: routine research, qualification, inbound/authorized outreach, buyer-requested payment requests, verified payment handling, predefined fulfillment and analytics may run automatically. Escalate refunds/disputes, money movement out, legal commitments, security/privacy incidents, sensitive or regulated matters, ambiguous payments, provider failures and complaints.
Never bypass platform rules, opt-outs, authentication or spending limits.
When asked to act, explain the action and use available system state; do not claim an external action happened unless the system actually performed it.
"""

def status():
    def read(name, default):
        p=STATE/name
        try: return json.loads(p.read_text(encoding="utf-8")) if p.exists() else default
        except Exception: return default
    return {
        "operator": read("operator_last_run.json", {}),
        "commercial": read("agent_team.json", {}),
        "channels": read("channel_readiness.json", {}),
        "policy": read("operator_policy.json", {}),
        "autonomy": "exception_only",
    }

def local_reply(message):
    s=status()
    m=message.lower()
    if any(x in m for x in ("status","health","how are we","what is happening")):
        c=s["commercial"]; op=s["operator"]
        return {
            "reply": f"Growth Stack Agent OS is online. Autonomy: exception-only. "
                     f"Mission target: KES {c.get('target_kes',1000000):,}. "
                     f"Last operator run status: {op.get('cycles',[{}])[-1].get('health',{}).get('status','not yet recorded') if op.get('cycles') else 'not yet recorded'}. "
                     f"I can coordinate research, offers, sales, payments and operations, while escalating defined exceptions.",
            "mode":"local_operator"
        }
    if "team" in m or "agents" in m:
        team=s["commercial"].get("team",[])
        return {"reply":"The Agent OS currently has "+str(len(team))+" specialist roles: CEO/Strategy, Scout, Research, Offer, Prospecting, Sales, Follow-up, Solutions, Demo, Customer Success, Finance, Risk/Governance and Growth Optimizer.","mode":"local_operator"}
    return {"reply":"I am connected to the Growth Stack control plane, but the language-model provider is not configured yet. I can still report system state. Once an OPENAI_API_KEY (or another approved OpenAI-compatible provider) is configured, this same interface becomes the full conversational Agent OS.","mode":"local_operator"}

def llm_reply(message, history):
    key=os.getenv("OPENAI_API_KEY","")
    if not key:
        return local_reply(message)
    base=os.getenv("OPENAI_BASE_URL","https://api.openai.com/v1").rstrip("/")
    model=os.getenv("GROWTH_AGENT_MODEL", os.getenv("OPENAI_MODEL","gpt-5.6"))
    payload={"model":model,"messages":[{"role":"system","content":SYSTEM_PROMPT}]+history[-12:]+[{"role":"user","content":message}],"temperature":0.2}
    req=Request(base+"/chat/completions",data=json.dumps(payload).encode(),headers={"Authorization":"Bearer "+key,"Content-Type":"application/json"},method="POST")
    try:
        with urlopen(req,timeout=45) as r:
            data=json.loads(r.read().decode())
        return {"reply":data["choices"][0]["message"]["content"],"mode":"llm"}
    except (HTTPError,URLError,KeyError,ValueError,TimeoutError) as exc:
        return {"reply":"The language-model provider is temporarily unavailable. The control plane is still running safely. Error class: "+type(exc).__name__,"mode":"fallback"}

def chat(message, history=None):
    message=(message or "").strip()
    if not message: raise ValueError("message is required")
    return llm_reply(message, history or [])
