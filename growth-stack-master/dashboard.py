"""Generate a lightweight monitoring dashboard as HTML."""
from __future__ import annotations

import html
import json
from pathlib import Path
from datetime import datetime, timezone

from monitor import check
from research_loop import top_opportunities, build_research_queue

ROOT = Path(__file__).resolve().parent
STATE = ROOT / "state"
OUT = ROOT / "MONITORING_DASHBOARD.html"


def render() -> str:
    health = check()
    top = top_opportunities(15)
    rows = []
    for item in top:
        rows.append(
            "<tr>"
            f"<td>{html.escape(str(item.get('score','')))}</td>"
            f"<td>{html.escape(str(item.get('market','')))}</td>"
            f"<td>{html.escape(str(item.get('sector','')))}</td>"
            f"<td>{html.escape(str(item.get('type','')))}</td>"
            f"<td>{html.escape(str(item.get('demand_signal','')))}</td>"
            f"<td>{html.escape(str(item.get('recommended_offer','')))}</td>"
            "</tr>"
        )
    status = health["status"]
    return f"""<!doctype html>
<html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>
<title>Growth Stack Master Monitor</title>
<style>body{{font-family:system-ui;margin:20px;max-width:1200px}}.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px}}.card{{border:1px solid #ddd;border-radius:12px;padding:14px}}table{{width:100%;border-collapse:collapse;margin-top:20px}}th,td{{padding:8px;border-bottom:1px solid #ddd;text-align:left;font-size:14px}}.status{{font-size:24px;font-weight:700}}</style></head>
<body><h1>Growth Stack Master</h1><p>Execution + Research Monitoring Dashboard</p>
<div class='grid'><div class='card'><div class='status'>{html.escape(status)}</div><small>System health</small></div>
<div class='card'><b>{len(build_research_queue())}</b><br><small>Research combinations</small></div>
<div class='card'><b>{health['opportunities']}</b><br><small>Stored opportunities</small></div>
<div class='card'><b>{health['timestamp']}</b><br><small>Last monitor check</small></div></div>
<h2>Top opportunities</h2><table><tr><th>Score</th><th>Market</th><th>Sector</th><th>Type</th><th>Demand</th><th>Offer</th></tr>{''.join(rows)}</table>
<h2>Control policy</h2><p>Research and internal analysis may run automatically. External outreach, spending, contracts, refunds, payment movement, sensitive publication, deletion and legal/regulatory commitments remain approval-gated.</p>
</body></html>"""


if __name__ == "__main__":
    OUT.write_text(render(), encoding="utf-8")
    print(OUT)
