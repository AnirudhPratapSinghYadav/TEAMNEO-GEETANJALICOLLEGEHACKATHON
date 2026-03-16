"""Hybrid detector — combines regex and NER results for higher accuracy."""

from typing import Any, Dict, List

from . import ner_detector
from . import regex_detector

# TODO: implement result merging / deduplication logic using regex_detector and ner_detector


def detect(text: str, user_context: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Detect PII and sensitive data in *text* using hybrid regex + NER approach.

    Returns a list of detected entity dicts, each with at minimum:
        {"entity_type": str, "text": str, "start": int, "end": int, "score": float}
    """
    # Stub: return empty list until regex/NER detectors are implemented.
    return []
