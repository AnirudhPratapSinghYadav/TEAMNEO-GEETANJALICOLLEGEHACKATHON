"""Decision engine — determines the final action (ALLOW / BLOCK / REDACT / TRANSFORM)."""

from typing import Any, Dict, List

# TODO: implement decision logic based on risk score and active policies


def decide(
    risk_score: float,
    entities: List[Dict[str, Any]],
    policies: List[Dict[str, Any]],
    user_context: Dict[str, Any],
) -> Dict[str, Any]:
    """Determine the governance action for this request.

    Returns a dict with at minimum:
        {"decision": str, "message": str}
    where *decision* is one of APPROVE, REDACT, BLOCK, or ESCALATE.
    Optional keys:
        "redacted_prompt": str  — present when decision == "REDACT"
    """
    # Stub: always approve until decision logic is implemented.
    return {"decision": "APPROVE", "message": "Request approved by AEGIS governance pipeline."}
