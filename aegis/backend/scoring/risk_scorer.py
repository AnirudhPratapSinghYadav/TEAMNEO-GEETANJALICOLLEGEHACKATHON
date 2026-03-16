"""Risk scorer — aggregates detection signals into a single risk score."""

from typing import Any, Dict, List

# TODO: implement composite risk scoring logic


def calculate(
    entities: List[Dict[str, Any]],
    policies: List[Dict[str, Any]],
    user_context: Dict[str, Any],
) -> Dict[str, Any]:
    """Compute a composite risk score from detected entities and matched policies.

    Returns a dict with at minimum:
        {"score": float, "breakdown": Dict[str, float]}
    where *score* is in the range [0.0, 1.0].
    """
    # Stub: zero risk until scoring logic is implemented.
    return {"score": 0.0, "breakdown": {}}
