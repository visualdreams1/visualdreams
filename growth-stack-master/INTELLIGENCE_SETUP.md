# Growth Stack Intelligence + Business Acquisition Layer

## Search providers

Required:
- `TAVILY_API_KEY` — live web research.

Optional additional discovery providers:
- `BRAVE_SEARCH_API_KEY` — Brave Web Search + Brave Place Search.
- `GOOGLE_CSE_API_KEY` + `GOOGLE_CSE_ID` — Google Programmable Search / Custom Search JSON API.
- `SERPER_API_KEY` — Google-results API provider.
- `OPENAI_API_KEY` — optional evidence synthesis/reasoning.

The pipeline merges whichever providers are configured. It does not claim to query literally every search engine; providers without a permitted API are not scraped or bypassed.

## Business extraction pipeline

`SEARCH → MULTI-PROVIDER MERGE → INDIVIDUAL BUSINESS DISCOVERY → PUBLIC PAGE RESOLUTION → CONTACT EXTRACTION → CONTACT VERIFICATION → PRIMARY CHANNEL RANKING → DEDUPE → CRM → PERSONALIZED SALES QUEUE → FOLLOW-UP → REPLY CLASSIFICATION → METRICS`

For public business pages the extractor looks for schema.org business data, public email, telephone, explicit WhatsApp links, public LinkedIn/social profiles and public contact pages. Every contact keeps its source URL and confidence. It never guesses a contact or bypasses login/CAPTCHA/access controls.

## Technical controls

- Research cursor rotates through the full 16,720-opportunity matrix instead of repeatedly scanning only the first batch.
- `DISCOVERY_RESULTS_PER_QUERY` controls search result count.
- `DISCOVERY_MAX_PAGES_PER_QUERY` controls public-page enrichment.
- `DISCOVERY_DELAY_SECONDS` controls fetch pacing.
- Contact verification ranks public channels and rejects malformed values.
- `state/inbound_replies.jsonl` can receive provider webhook events; the outcome engine classifies STOP/BOUNCE/POSITIVE/NEGATIVE/QUESTION and suppresses future follow-ups where appropriate.
- `state/sales_metrics.json` records lead, send, engagement and opt-out metrics.

## Every 6 hours

1. Research rotates to the next opportunity batch.
2. Evidence is refreshed and scored.
3. Configured search providers discover individual businesses.
4. Public pages are resolved and contact channels extracted.
5. Contacts are verified, deduplicated and ranked.
6. CRM and follow-up plans are updated.
7. Business-specific sales messages are prepared.
8. Replies, opt-outs and metrics are processed.
9. Dashboard/state files are committed.

## Safety

Outbound sending remains approval-gated. Even if a sender webhook is configured, the queue must contain `APPROVED_TO_SEND`, and the explicit outbound switch must be enabled. STOP/opt-out/bounce states suppress future follow-ups.

## Manual run

Use GitHub Actions → **Growth Stack Intelligence** → **Run workflow**.
