"""
Detection engine: regex-based PII, credential, and prompt-injection detection.
Returns a list of DetectedEntity objects with type, value (masked), and confidence.
"""
import re
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class DetectedEntity:
    entity_type: str          # e.g. EMAIL, PHONE, API_KEY, PROMPT_INJECTION
    category: str             # PII | CREDENTIAL | INJECTION | SENSITIVE
    value_masked: str         # masked representation
    confidence: float         # 0.0 – 1.0
    start: int = 0
    end: int = 0


# ---------------------------------------------------------------------------
# Regex patterns
# ---------------------------------------------------------------------------
_PATTERNS: List[tuple] = [
    # PII
    ("EMAIL",           "PII",        r'\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b',        0.95),
    ("PHONE_US",        "PII",        r'\b(\+1[\s\-]?)?(\(?\d{3}\)?[\s\-]?)(\d{3}[\s\-]?\d{4})\b',     0.90),
    ("SSN",             "PII",        r'\b\d{3}[-\s]?\d{2}[-\s]?\d{4}\b',                               0.95),
    ("CREDIT_CARD",     "PII",        r'\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13}|6(?:011|5[0-9]{2})[0-9]{12})\b', 0.95),
    ("IP_ADDRESS",      "PII",        r'\b(?:\d{1,3}\.){3}\d{1,3}\b',                                   0.75),
    ("DATE_OF_BIRTH",   "PII",        r'\b(?:dob|date of birth|born on|birthday)[:\s]+\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4}\b', 0.85),
    ("PERSON_NAME",     "PII",        r'\b(?:my name is|i am|i\'m|call me)\s+([A-Z][a-z]+(?:\s[A-Z][a-z]+)+)\b', 0.70),
    ("ADDRESS",         "PII",        r'\b\d{1,5}\s+[\w\s]{3,30},\s*[A-Za-z\s]+,\s*[A-Z]{2}\s+\d{5}\b', 0.80),
    ("PASSPORT",        "PII",        r'\b[A-Z]{1,2}\d{6,9}\b',                                          0.65),
    ("AADHAAR",         "PII",        r'\b\d{4}\s\d{4}\s\d{4}\b',                                        0.88),
    ("PAN_INDIA",       "PII",        r'\b[A-Z]{5}\d{4}[A-Z]\b',                                         0.88),
    # Credentials
    ("OPENAI_API_KEY",  "CREDENTIAL", r'\bsk-[A-Za-z0-9]{20,}\b',                                        0.99),
    ("ANTHROPIC_KEY",   "CREDENTIAL", r'\bsk-ant-[A-Za-z0-9\-_]{20,}\b',                                 0.99),
    ("AWS_ACCESS_KEY",  "CREDENTIAL", r'\bAKIA[0-9A-Z]{16}\b',                                           0.99),
    ("AWS_SECRET_KEY",  "CREDENTIAL", r'\b[A-Za-z0-9+/]{40}\b',                                          0.70),
    ("GITHUB_TOKEN",    "CREDENTIAL", r'\bghp_[A-Za-z0-9]{36}\b',                                        0.99),
    ("GITHUB_TOKEN2",   "CREDENTIAL", r'\bgithub_pat_[A-Za-z0-9_]{59}\b',                                0.99),
    ("GENERIC_SECRET",  "CREDENTIAL", r'(?i)(?:password|passwd|secret|token|api[_\-]?key|auth[_\-]?token)\s*[:=]\s*["\']?([A-Za-z0-9!@#$%^&*\-_+=]{8,})["\']?', 0.85),
    ("PRIVATE_KEY",     "CREDENTIAL", r'-----BEGIN (?:RSA |EC |OPENSSH |PGP )?PRIVATE KEY-----',         0.99),
    ("BEARER_TOKEN",    "CREDENTIAL", r'\bBearer\s+[A-Za-z0-9\-._~+/]+=*\b',                             0.90),
    # Sensitive financial
    ("BANK_ACCOUNT",    "SENSITIVE",  r'\b\d{8,17}\b',                                                    0.55),
    ("SALARY_INFO",     "SENSITIVE",  r'(?i)\bsalar(?:y|ies)\b.*?\$[\d,]+',                               0.75),
    # Prompt injection
    ("PROMPT_INJECTION_IGNORE",  "INJECTION", r'(?i)ignore\s+(?:all\s+)?(?:previous|prior|above)\s+instructions?', 0.98),
    ("PROMPT_INJECTION_JAILBREAK","INJECTION", r'(?i)(?:do\s+anything\s+now|dan\s+mode|jailbreak|bypass\s+(?:safety|filter|restriction|policy))', 0.97),
    ("PROMPT_INJECTION_ROLE",    "INJECTION", r'(?i)(?:you\s+are\s+now|pretend\s+you\s+are|act\s+as\s+(?:a\s+)?(?:hacker|evil|malicious|unrestricted))', 0.90),
    ("PROMPT_INJECTION_SYSTEM",  "INJECTION", r'(?i)(?:system\s*:\s*you|<\s*system\s*>|disregard\s+(?:your\s+)?(?:instructions?|guidelines?|rules?))', 0.92),
    ("PROMPT_INJECTION_EXFIL",   "INJECTION", r'(?i)(?:send|email|exfil(?:trate)?|leak|dump)\s+(?:the\s+)?(?:data|information|context|system\s+prompt)', 0.88),
    ("PROMPT_INJECTION_REPEAT",  "INJECTION", r'(?i)repeat\s+(?:everything|all|the\s+(?:above|following))\s+(?:back|verbatim|word)', 0.85),
]

_COMPILED = [(name, cat, re.compile(pat, re.IGNORECASE), conf) for name, cat, pat, conf in _PATTERNS]


def _mask(value: str) -> str:
    """Mask a sensitive value, keeping first/last chars."""
    if len(value) <= 4:
        return "*" * len(value)
    return value[:2] + "*" * (len(value) - 4) + value[-2:]


def detect(text: str) -> List[DetectedEntity]:
    """
    Run all detectors on text and return a deduplicated list of DetectedEntity.
    """
    entities: List[DetectedEntity] = []
    seen_spans: set = set()

    for name, cat, pattern, conf in _COMPILED:
        for m in pattern.finditer(text):
            span = (m.start(), m.end())
            # Skip overlapping spans (keep higher confidence match)
            overlap = any(
                not (span[1] <= s[0] or span[0] >= s[1])
                for s in seen_spans
            )
            if overlap:
                continue
            seen_spans.add(span)
            raw = m.group(0)
            masked = _mask(raw)
            entities.append(DetectedEntity(
                entity_type=name,
                category=cat,
                value_masked=masked,
                confidence=conf,
                start=m.start(),
                end=m.end(),
            ))

    # Sort by confidence descending
    entities.sort(key=lambda e: e.confidence, reverse=True)
    return entities


def redact(text: str, entities: Optional[List[DetectedEntity]] = None) -> str:
    """Replace detected sensitive values with [REDACTED:<type>] tags."""
    if entities is None:
        entities = detect(text)
    # Sort by start position descending for safe in-place replacement
    sorted_entities = sorted(entities, key=lambda e: e.start, reverse=True)
    chars = list(text)
    for ent in sorted_entities:
        replacement = f"[REDACTED:{ent.entity_type}]"
        chars[ent.start:ent.end] = list(replacement)
    return "".join(chars)


def compute_risk_score(entities: List[DetectedEntity]) -> float:
    """
    Compute an overall risk score 0.0–1.0 based on detected entities.
    """
    if not entities:
        return 0.0

    weights = {"INJECTION": 0.9, "CREDENTIAL": 0.85, "PII": 0.6, "SENSITIVE": 0.5}
    score = 0.0
    for ent in entities:
        w = weights.get(ent.category, 0.4)
        score = max(score, w * ent.confidence)

    # Accumulate a slight penalty for volume
    bonus = min(0.15, len(entities) * 0.02)
    return min(1.0, round(score + bonus, 3))
