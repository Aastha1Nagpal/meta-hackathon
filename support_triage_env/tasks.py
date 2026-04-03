from __future__ import annotations

from typing import Dict, List, Literal

from pydantic import BaseModel, Field


class TaskSpec(BaseModel):
    task_id: str
    difficulty: Literal["easy", "medium", "hard"]
    title: str
    objective: str
    ticket_id: str
    customer_tier: str
    customer_message: str
    hints: List[str] = Field(default_factory=list)
    expected_priority: str
    expected_team: str
    required_tags: List[str]
    required_reply_phrases: List[str]
    forbidden_reply_phrases: List[str] = Field(default_factory=list)
    expected_resolution: str


TASKS: Dict[str, TaskSpec] = {
    "duplicate_refund": TaskSpec(
        task_id="duplicate_refund",
        difficulty="easy",
        title="Resolve a duplicate billing charge request",
        objective=(
            "Triage the ticket, route it to billing, and prepare a reassuring response that "
            "acknowledges the duplicate charge and next refund steps."
        ),
        ticket_id="TCK-1001",
        customer_tier="standard",
        customer_message=(
            "Hi team, I was charged twice for my March subscription renewal. "
            "I only have one workspace and both charges hit the same card today. "
            "Can someone reverse the extra payment?"
        ),
        hints=[
            "A strong reply should apologize, mention the refund, and set a realistic timeline.",
            "Billing owns the operational follow-up here.",
        ],
        expected_priority="medium",
        expected_team="billing",
        required_tags=["refund_requested", "duplicate_charge"],
        required_reply_phrases=["sorry", "refund", "48 hours"],
        expected_resolution="refund_review_opened",
    ),
    "phishing_escalation": TaskSpec(
        task_id="phishing_escalation",
        difficulty="medium",
        title="Escalate a phishing and account security incident",
        objective=(
            "Recognize the phishing risk, route the ticket to security, and draft safe guidance "
            "without asking the customer to share secrets."
        ),
        ticket_id="TCK-2044",
        customer_tier="pro",
        customer_message=(
            "I got an email saying my workspace will be suspended unless I verify my password "
            "through a link. The sender looked odd, but one of my teammates already clicked it. "
            "What should we do right now?"
        ),
        hints=[
            "The response should tell the customer not to click suspicious links.",
            "Password resets and security escalation are both appropriate.",
        ],
        expected_priority="high",
        expected_team="security",
        required_tags=["phishing", "account_security"],
        required_reply_phrases=["do not click", "reset your password", "forward the email"],
        forbidden_reply_phrases=["share your password"],
        expected_resolution="escalated_to_security",
    ),
    "enterprise_outage_credit": TaskSpec(
        task_id="enterprise_outage_credit",
        difficulty="hard",
        title="Handle a VIP outage plus SLA credit request",
        objective=(
            "Triage a revenue-critical incident for an enterprise customer, route it to incident "
            "response, and send an operations-style reply that addresses both outage handling and SLA credit."
        ),
        ticket_id="TCK-3307",
        customer_tier="enterprise_vip",
        customer_message=(
            "Our entire APAC support team cannot load dashboards after your 07:10 deploy and we have "
            "customers waiting. We are on an enterprise annual contract and will expect SLA credit if this "
            "is not fixed immediately. Please confirm who owns this and how often you will update us."
        ),
        hints=[
            "This is an urgent production incident for a VIP account.",
            "A complete response should mention the incident, engineering ownership, SLA credit handling, and update cadence.",
        ],
        expected_priority="urgent",
        expected_team="incident_response",
        required_tags=["outage", "sla_credit", "vip_customer"],
        required_reply_phrases=["incident", "engineering", "sla credit", "hourly updates"],
        expected_resolution="incident_escalated",
    ),
}


def list_tasks() -> List[TaskSpec]:
    return [
        TASKS["duplicate_refund"],
        TASKS["phishing_escalation"],
        TASKS["enterprise_outage_credit"],
    ]
