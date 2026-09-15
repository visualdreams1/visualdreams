# Growth Stack Master — Quickstart

## Run locally

Python 3.10+ is recommended.

```bash
cd growth-stack-master
python operator.py
```

The first run creates `state/business_state.json` and `state/activity.log`, then creates Mission 001's execution queue.

## What V0.1 does

- Stores business state locally.
- Creates and prioritizes tasks.
- Separates READY, WAITING_APPROVAL and DONE states.
- Records approvals and completion results.
- Stores prospects.
- Produces a simple control-room dashboard.
- Requires no external Python packages.

## Safety boundary

V0.1 does **not** send messages, spend money, access payment accounts, or execute external business actions. Those capabilities will be connected only through explicit tools and approval gates.

## Next build layer

1. Model adapter (replaceable AI provider).
2. Web/research tool.
3. File/knowledge memory.
4. CRM and lead tools.
5. Human approval queue.
6. Monitoring dashboard.
7. Messaging integrations.
8. Automated daily business cycle.
