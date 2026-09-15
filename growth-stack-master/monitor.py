"""Health monitor and HTML dashboard for Growth Stack intelligence."""
from __future__ import annotations
import json, html
from datetime import datetime, timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parent; STATE=ROOT/"state"

def load(name, default):
 p=STATE/name
 try:return json.loads(p.read_text(encoding="utf-8")) if p.exists() else default
 except Exception:return default

def check():
 health=load("intelligence_health.json",{})
 queue=load("decision_queue.json",[])
 errors=[]; warnings=[]
 if not (STATE/"opportunities.json").exists(): warnings.append("Research store not created yet")
 if not queue: warnings.append("Decision queue is empty")
 status=health.get("status","NOT_RUN")
 if errors: status="DEGRADED"
 report={"timestamp":datetime.now(timezone.utc).isoformat(),"status":status,"errors":errors,"warnings":warnings,"checks":{"state_directory":STATE.exists(),"research_store":(STATE/"opportunities.json").exists(),"decision_queue":(STATE/"decision_queue.json").exists(),"intelligence_health":(STATE/"intelligence_health.json").exists()}}
 STATE.mkdir(exist_ok=True); (STATE/"health.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
 rows=[]
 for x in queue[:50]:
  rows.append(f"<tr><td>{html.escape(str(x.get('status','')))}</td><td>{html.escape(str(x.get('market','')))}</td><td>{html.escape(str(x.get('sector','')))}</td><td>{html.escape(str(x.get('type','')))}</td><td>{x.get('score',0)}</td><td>{x.get('confidence',0)}</td><td>{x.get('independent_sources',0)}</td><td>{html.escape(str(x.get('change_type','')))}</td></tr>")
 page=f'''<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Growth Stack Monitor</title><style>body{{font-family:system-ui;margin:24px}}.card{{display:inline-block;border:1px solid #ddd;border-radius:12px;padding:14px;margin:5px;min-width:120px}}table{{border-collapse:collapse;width:100%;margin-top:20px}}th,td{{border:1px solid #ddd;padding:7px;text-align:left}}th{{background:#f4f4f4}}</style></head><body><h1>Growth Stack Global — Intelligence Monitor</h1><p>{datetime.now(timezone.utc).isoformat()}</p><div class="card"><b>Status</b><br>{html.escape(status)}</div><div class="card"><b>Analysed</b><br>{health.get('items_analysed',0)}</div><div class="card"><b>Approval candidates</b><br>{health.get('approval_candidates',0)}</div><div class="card"><b>New/changed</b><br>{health.get('new_or_changed',0)}</div><div class="card"><b>AI enabled</b><br>{health.get('ai_enabled',False)}</div><table><tr><th>Status</th><th>Market</th><th>Sector</th><th>Opportunity</th><th>Score</th><th>Confidence</th><th>Sources</th><th>Change</th></tr>{''.join(rows)}</table><p><b>Safety:</b> research and recommendations may run automatically; consequential external actions remain approval-gated.</p></body></html>'''
 (ROOT/"MONITORING_DASHBOARD.html").write_text(page,encoding="utf-8")
 return report
if __name__=="__main__": print(json.dumps(check(),indent=2))
