"""
Core governance engine.
Takes a prompt + department, runs detection, applies policy, returns a GovernanceResult.
"""
import uuid
from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime

from detector import detect, redact, compute_risk_score, DetectedEntity
from policies import get_policy, Policy


DECISION_APPROVE = "APPROVE"
DECISION_REDACT = "REDACT"
DECISION_BLOCK = "BLOCK"
DECISION_ESCALATE = "ESCALATE"


@dataclass
class GovernanceResult:
    request_id: str
    decision: str
    risk_score: float
    entities: List[DetectedEntity]
    policy_matches: List[str]
    remediation: List[str]
    explanation: str
    redacted_prompt: Optional[str]
    timestamp: datetime = field(default_factory=datetime.utcnow)


def _build_explanation(
    decision: str,
    risk_score: float,
    entities: List[DetectedEntity],
    policy: Policy,
    policy_matches: List[str],
) -> str:
    entity_summary = ", ".join(
        f"{e.entity_type} ({e.category}, conf={e.confidence:.0%})"
        for e in entities[:5]
    ) or "none"
    extra = f" ({len(entities) - 5} more)" if len(entities) > 5 else ""

    base = (
        f"Decision: {decision}. Risk score: {risk_score:.2f}/1.00. "
        f"Policy: {policy.name}. "
        f"Detected entities: {entity_summary}{extra}. "
    )
    if policy_matches:
        base += f"Triggered rules: {'; '.join(policy_matches)}. "

    rationale = {
        DECISION_APPROVE: "No sensitive content detected above threshold. Request forwarded to upstream LLM.",
        DECISION_REDACT:  "Sensitive content detected and automatically redacted. Modified prompt forwarded to upstream LLM.",
        DECISION_BLOCK:   "High-risk content or injection attempt detected. Request blocked to protect data integrity.",
        DECISION_ESCALATE: "Ambiguous or elevated-risk content requiring human review before processing.",
    }.get(decision, "")
    return base + rationale


def _build_remediation(decision: str, entities: List[DetectedEntity], policy: Policy) -> List[str]:
    rems = []
    categories = {e.category for e in entities}
    types = {e.entity_type for e in entities}

    if decision == DECISION_BLOCK:
        rems.append("Remove all sensitive content from your prompt before resubmitting.")
    if "INJECTION" in categories:
        rems.append("Detected prompt injection — review your prompt for adversarial instructions.")
    if "CREDENTIAL" in types or "CREDENTIAL" in categories:
        rems.append("Never include API keys, passwords, or tokens in LLM prompts.")
        rems.append("Use environment variables or a secrets manager instead.")
    if "PII" in categories:
        rems.append("Anonymize or pseudonymize personal data before sending to external AI services.")
    if decision == DECISION_ESCALATE:
        rems.append("Contact your data governance team for manual review and approval.")
    if not rems:
        rems.append("No remediation required.")
    return rems


def evaluate(
    prompt: str,
    department: str = "Default",
    user_id: Optional[str] = None,
    model: Optional[str] = None,
) -> GovernanceResult:
    """
    Main governance evaluation function.
    Returns a GovernanceResult with decision, risk score, entities, and explanation.
    """
    request_id = str(uuid.uuid4())
    policy = get_policy(department)
    entities = detect(prompt)
    risk_score = compute_risk_score(entities)

    entity_types = {e.entity_type for e in entities}
    entity_categories = {e.category for e in entities}
    policy_matches: List[str] = []
    decision = DECISION_APPROVE

    # --- Rule evaluation (priority: BLOCK > ESCALATE > REDACT > APPROVE) ---

    # Check hard-block entity types
    blocked_types = entity_types & policy.block_entity_types
    if blocked_types:
        decision = DECISION_BLOCK
        policy_matches.extend(
            f"BLOCK rule: entity type '{t}' is prohibited in {policy.name}" for t in blocked_types
        )

    # Check block categories
    blocked_cats = entity_categories & policy.block_categories
    if blocked_cats:
        decision = DECISION_BLOCK
        policy_matches.extend(
            f"BLOCK rule: category '{c}' is prohibited in {policy.name}" for c in blocked_cats
        )

    # Score-based block
    if risk_score >= policy.block_score_threshold and decision != DECISION_BLOCK:
        decision = DECISION_BLOCK
        policy_matches.append(
            f"BLOCK rule: risk score {risk_score:.2f} >= threshold {policy.block_score_threshold}"
        )

    # Escalate
    if decision == DECISION_APPROVE:
        escalate_types = entity_types & policy.escalate_entity_types
        if escalate_types:
            decision = DECISION_ESCALATE
            policy_matches.extend(
                f"ESCALATE rule: entity type '{t}' requires review in {policy.name}"
                for t in escalate_types
            )
        elif risk_score >= policy.escalate_score_threshold:
            decision = DECISION_ESCALATE
            policy_matches.append(
                f"ESCALATE rule: risk score {risk_score:.2f} >= threshold {policy.escalate_score_threshold}"
            )

    # Redact
    if decision == DECISION_APPROVE:
        redact_cats = entity_categories & policy.redact_categories
        if redact_cats:
            decision = DECISION_REDACT
            policy_matches.extend(
                f"REDACT rule: category '{c}' must be masked in {policy.name}" for c in redact_cats
            )
        elif risk_score >= policy.redact_score_threshold:
            decision = DECISION_REDACT
            policy_matches.append(
                f"REDACT rule: risk score {risk_score:.2f} >= threshold {policy.redact_score_threshold}"
            )

    # Model allow-list check
    if model and policy.allowed_models and model not in policy.allowed_models:
        if decision not in (DECISION_BLOCK,):
            decision = DECISION_BLOCK
            policy_matches.append(
                f"BLOCK rule: model '{model}' is not in allowed list for {policy.name}"
            )

    redacted_prompt = None
    if decision == DECISION_REDACT:
        redacted_prompt = redact(prompt, entities)

    explanation = _build_explanation(decision, risk_score, entities, policy, policy_matches)
    remediation = _build_remediation(decision, entities, policy)

    return GovernanceResult(
        request_id=request_id,
        decision=decision,
        risk_score=risk_score,
        entities=entities,
        policy_matches=policy_matches,
        remediation=remediation,
        explanation=explanation,
        redacted_prompt=redacted_prompt,
    )
