"""Policy engine — evaluates active policies against detection results."""

from typing import Any, Dict, List

# TODO: implement policy loading and evaluation logic


def evaluate(entities: List[Dict[str, Any]], user_context: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Evaluate active policies against detected entities and user context.

    Returns a list of matched policy dicts, each with at minimum:
        {"name": str, "action": str, "severity": str}
    """
    # Stub: no policies matched until the policy store is implemented.
    return []
