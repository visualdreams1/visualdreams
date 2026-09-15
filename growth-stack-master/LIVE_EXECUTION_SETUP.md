# Growth Stack Live Execution Layer

## What is now connected
- Tavily live web search adapter
- Worldwide opportunity matrix
- Scheduled GitHub Actions execution every 6 hours
- Persistent opportunity state
- Health monitor
- HTML monitoring dashboard
- Manual `workflow_dispatch` trigger

Tavily is used as the first live provider because its current API supports search plus extraction/crawl/research capabilities for agents. The provider is isolated so another search provider can be added later without rewriting the business loop.

## One required owner action
Add a GitHub Actions repository secret named `TAVILY_API_KEY`.

Do not put the API key into Python files, `.md` files, commits, or chat messages.

## Runtime
The scheduled workflow runs:
1. `run_live_research.py`
2. `monitor.py`
3. `dashboard.py`
4. commits refreshed research state/dashboard when changed

## Safety
The scheduler researches and organizes information. It does NOT send customer messages, spend money, move M-Pesa funds, sign contracts, issue refunds, delete business data, or make legal/regulatory commitments.

## Monitoring
Open `MONITORING_DASHBOARD.html` after a workflow run. It shows health, research coverage, stored opportunities and the current top-ranked opportunities.

## Next execution upgrades
- multi-provider fallback
- evidence freshness/change detection
- source credibility scoring
- AI synthesis/ranking adapter
- approval queue integration
- lead discovery and CRM
- customer outreach after explicit owner approval
