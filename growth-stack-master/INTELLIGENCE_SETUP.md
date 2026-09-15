# Growth Stack Intelligence Layer

## Required GitHub Actions secrets

Add these repository secrets under GitHub Settings → Secrets and variables → Actions:

- `TAVILY_API_KEY` — required for live web research.
- `OPENAI_API_KEY` — optional for AI evidence synthesis and stronger reasoning.

The system still performs deterministic evidence scoring when `OPENAI_API_KEY` is absent.

## What happens every 6 hours

1. Tavily searches the worldwide opportunity matrix.
2. Existing opportunities are refreshed so changes can be detected.
3. Evidence is normalized and independent sources are counted.
4. The intelligence engine scores evidence quality and confidence.
5. Optional GPT-5.6 Luna analysis reads the supplied evidence only.
6. The engine detects NEW, NEW_EVIDENCE, STRENGTHENING, WEAKENING and STABLE signals.
7. Opportunities are ranked into the decision queue.
8. `DECISION_QUEUE.md`, `MONITORING_DASHBOARD.html` and machine-readable state are updated.
9. GitHub commits the resulting research state.

## Decision rule

High-scoring opportunities with adequate independent evidence become `APPROVAL_REQUIRED`, not automatic sales actions. The system never sends outreach, signs contracts, spends money, moves payments or publishes sensitive material without owner approval.

## Manual run

Use GitHub Actions → Growth Stack Intelligence → Run workflow.

## Cost control

The scheduled job researches a bounded batch each run rather than attempting all combinations at once. The matrix is much larger than the per-run batch; subsequent runs refresh different/previously stored opportunities as the system evolves.
