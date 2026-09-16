# Growth Stack Autonomous Sales Engine

## Operating model
SEARCH → DISCOVER → VERIFY → DEDUPE → SCORE → PERSONALIZE → QUEUE → APPROVAL → SEND → REPLY → SUPPRESS/ENGAGE → METRICS → LEARN.

## What is autonomous
- Scheduled research and business discovery.
- Public contact extraction and verification.
- CRM updates, deduplication and scoring.
- Personalized sales-message generation from observed evidence.
- Follow-up scheduling and reply classification.
- Metrics and monitoring.

## What remains deliberately gated
External outreach requires a legitimate sender provider, configured webhook, and `OUTBOUND_ENABLED=true`. This prevents accidental or unauthorized messages. The system must not bypass login, CAPTCHA, access controls, robots restrictions, or provider limits.

## Required secrets
- `TAVILY_API_KEY`
- At least one additional search provider is recommended: `BRAVE_SEARCH_API_KEY`, `GOOGLE_CSE_API_KEY` + `GOOGLE_CSE_ID`, or `SERPER_API_KEY`.
- `OPENAI_API_KEY` is optional for AI synthesis.
- `SALES_SENDER_WEBHOOK` is required for actual outbound delivery.
- `OUTBOUND_ENABLED` must be explicitly enabled for delivery.

## User checklist
1. Add the API secrets in GitHub repository Settings → Secrets and variables → Actions.
2. Configure a legitimate business messaging/email sender that accepts the sales webhook payload.
3. Test the sender with the owner's own number before contacting prospects.
4. Confirm the test delivery.
5. Review the first small batch of queued prospects/messages.
6. Enable outbound only after the sender and opt-out handling are confirmed.

The engine should never invent contact information or claim delivery when the sender has not returned a successful response.
