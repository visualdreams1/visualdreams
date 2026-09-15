# Growth Stack Master Memory

The Master Agent keeps these records separate so the business can be moved between AI providers without losing institutional knowledge.

## 1. Company Memory
- company_name
- mission
- owner
- target_markets
- positioning
- constraints
- assets
- current_strategy
- current_priority

## 2. Product Catalog
For every service:
- product_id
- name
- customer_problem
- promised_outcome
- target_vertical
- delivery_method
- setup_price
- recurring_price
- estimated_delivery_time
- required_tools
- proof/demo
- status

## 3. CRM
For every lead/customer:
- contact_name
- business
- vertical
- location
- contact_channel
- problem
- stage
- last_contact
- next_action
- estimated_value
- notes
- consent/status where applicable

Stages: RESEARCHED → QUALIFIED → CONTACTED → RESPONDED → DISCOVERY → PROPOSAL → WON → ONBOARDING → ACTIVE → RETENTION → LOST

## 4. Money Ledger
- date
- transaction_type
- description
- amount
- currency
- customer/project
- payment_status
- recurring
- notes

## 5. Knowledge Base
Store reusable:
- successful sales messages
- objections and responses
- proposals
- workflows
- technical patterns
- customer lessons
- market research
- experiments
- failures and fixes

## 6. Decision Log
For significant decisions:
- date
- decision
- reason
- evidence
- owner approval required?
- outcome
- lesson

## 7. Security Log
Track important access and security events without storing raw secrets.

Never store passwords, API keys, payment credentials, or other secrets in this memory file.
