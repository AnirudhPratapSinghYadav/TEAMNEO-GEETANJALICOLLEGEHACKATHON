"""Receipt generator — produces audit receipts (JSON / PDF) for each intercepted request."""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List

# TODO: implement JSON and PDF receipt generation (reportlab for PDF)


def generate(
    request_id: str,
    user_context: Dict[str, Any],
    prompt: str,
    entities: List[Dict[str, Any]],
    policies: List[Dict[str, Any]],
    risk_result: Dict[str, Any],
    decision_result: Dict[str, Any],
    processing_time_ms: float,
) -> Dict[str, Any]:
    """Generate a JSON audit receipt for an intercepted request.

    Returns a dict representing the receipt.
    """
    return {
        "receipt_id": str(uuid.uuid4()),
        "request_id": request_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "user": user_context,
        "entities_detected": entities,
        "policies_matched": policies,
        "risk_score": risk_result.get("score", 0.0),
        "risk_breakdown": risk_result.get("breakdown", {}),
        "decision": decision_result.get("decision", "APPROVE"),
        "decision_message": decision_result.get("message", ""),
        "processing_time_ms": processing_time_ms,
    }
