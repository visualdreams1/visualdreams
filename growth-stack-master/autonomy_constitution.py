"""Growth Stack autonomy constitution: the rules every autonomous cycle must obey."""
from __future__ import annotations
import json, os
from pathlib import Path
from datetime import datetime, timezone
ROOT=Path(__file__).resolve().parent; STATE=ROOT/"state"; STATE.mkdir(exist_ok=True)
CONSTITUTION={
 "version":"3.0",
 "mission":"Create measurable customer value and durable revenue while preserving customer choice, platform compliance and owner control.",
 "autonomous":True,
 "owner_is_exception_handler":True,
 "allowed_without_human": [
   "research_public_business_information",
   "score_and_prioritize_verified_prospects",
   "respond_to_inbound_or_opted_in_customers",
   "send_approved_policy_compliant_business_outreach",
   "qualify_needs",
   "quote_catalog_products",
   "create_orders_after_buyer_intent",
   "issue_buyer_requested_payment_request",
   "verify_provider_payment_callbacks",
   "start_predefined_fulfillment",
   "send_transactional_followups",
   "measure_and_optimize"
 ],
 "mandatory_escalation": [
   "refund_or_dispute","money_movement_out","legal_commitment",
   "security_incident","privacy_request","sensitive_or_regulated_topic",
   "customer_complaint","provider_failure","ambiguous_payment"
 ],
 "never": [
   "spam_or_bypass_platform_limits",
   "invent_contacts_identity_reviews_results_or_payments",
   "scrape_private_or_sensitive_personal_data",
   "continue after opt_out",
   "claim payment before verified callback",
   "change safety limits through self_learning",
   "spend funds without explicit configured budget",
   "self_replicate_or_change credentials/permissions"
 ],
 "resilience": {
   "idempotency_required":True,
   "provider_failover":True,
   "audit_every_external_action":True,
   "dry_run_default":True,
   "kill_switch_env":"GROWTH_KILL_SWITCH"
 },
 "created_at":datetime.now(timezone.utc).isoformat()
}
def load():
 p=STATE/"autonomy_constitution.json"
 if not p.exists(): p.write_text(json.dumps(CONSTITUTION,indent=2),encoding="utf-8")
 return CONSTITUTION
if __name__=="__main__": print(json.dumps(load(),indent=2))
