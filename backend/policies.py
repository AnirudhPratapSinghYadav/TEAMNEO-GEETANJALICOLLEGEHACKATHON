"""
Department-specific governance policies.
Each policy specifies thresholds and rules for APPROVE / REDACT / BLOCK / ESCALATE.
"""
from dataclasses import dataclass, field
from typing import List, Set


@dataclass
class Policy:
    name: str                         # department name
    block_categories: Set[str]        # entity categories that always BLOCK
    block_entity_types: Set[str]      # specific entity types that always BLOCK
    redact_categories: Set[str]       # categories to REDACT instead of BLOCK
    escalate_entity_types: Set[str]   # types that go to human review
    block_score_threshold: float      # risk score above which we BLOCK
    escalate_score_threshold: float   # risk score above which we ESCALATE
    redact_score_threshold: float     # risk score above which we REDACT
    allowed_models: List[str]         # empty = all models allowed
    description: str = ""


POLICIES: dict[str, Policy] = {
    "HR": Policy(
        name="HR",
        description="Human Resources — protect employee PII, salary data, and medical info.",
        block_categories={"CREDENTIAL", "INJECTION"},
        block_entity_types={"SSN", "CREDIT_CARD", "PRIVATE_KEY", "PROMPT_INJECTION_EXFIL"},
        redact_categories={"PII", "SENSITIVE"},
        escalate_entity_types={"SALARY_INFO", "DATE_OF_BIRTH", "AADHAAR", "PAN_INDIA"},
        block_score_threshold=0.85,
        escalate_score_threshold=0.65,
        redact_score_threshold=0.35,
        allowed_models=[],
    ),
    "Finance": Policy(
        name="Finance",
        description="Finance — protect financial records, credentials, and confidential data.",
        block_categories={"CREDENTIAL", "INJECTION"},
        block_entity_types={"CREDIT_CARD", "BANK_ACCOUNT", "SSN", "PRIVATE_KEY"},
        redact_categories={"PII", "SENSITIVE"},
        escalate_entity_types={"SALARY_INFO", "BANK_ACCOUNT"},
        block_score_threshold=0.80,
        escalate_score_threshold=0.60,
        redact_score_threshold=0.30,
        allowed_models=["gpt-4o", "gpt-4", "gpt-3.5-turbo", "claude-3-opus"],
    ),
    "Engineering": Policy(
        name="Engineering",
        description="Engineering — prevent credential leakage and code injection.",
        block_categories={"INJECTION"},
        block_entity_types={
            "OPENAI_API_KEY", "ANTHROPIC_KEY", "AWS_ACCESS_KEY", "AWS_SECRET_KEY",
            "GITHUB_TOKEN", "GITHUB_TOKEN2", "PRIVATE_KEY", "BEARER_TOKEN",
            "PROMPT_INJECTION_EXFIL",
        },
        redact_categories={"CREDENTIAL", "PII"},
        escalate_entity_types={"GENERIC_SECRET"},
        block_score_threshold=0.90,
        escalate_score_threshold=0.70,
        redact_score_threshold=0.40,
        allowed_models=[],
    ),
    "Legal": Policy(
        name="Legal",
        description="Legal — strict controls on all PII and confidential legal information.",
        block_categories={"CREDENTIAL", "INJECTION"},
        block_entity_types={"SSN", "PASSPORT", "CREDIT_CARD", "PRIVATE_KEY"},
        redact_categories={"PII", "SENSITIVE"},
        escalate_entity_types={"EMAIL", "PHONE_US", "ADDRESS"},
        block_score_threshold=0.75,
        escalate_score_threshold=0.55,
        redact_score_threshold=0.25,
        allowed_models=[],
    ),
    "Marketing": Policy(
        name="Marketing",
        description="Marketing — moderate PII controls, prevent credential exposure.",
        block_categories={"CREDENTIAL", "INJECTION"},
        block_entity_types={"PRIVATE_KEY"},
        redact_categories={"PII"},
        escalate_entity_types=set(),
        block_score_threshold=0.90,
        escalate_score_threshold=0.75,
        redact_score_threshold=0.40,
        allowed_models=[],
    ),
    "Default": Policy(
        name="Default",
        description="Default policy — balanced protection for all departments.",
        block_categories={"CREDENTIAL", "INJECTION"},
        block_entity_types={"PRIVATE_KEY", "SSN", "CREDIT_CARD"},
        redact_categories={"PII", "SENSITIVE"},
        escalate_entity_types=set(),
        block_score_threshold=0.85,
        escalate_score_threshold=0.70,
        redact_score_threshold=0.40,
        allowed_models=[],
    ),
}


def get_policy(department: str) -> Policy:
    return POLICIES.get(department, POLICIES["Default"])


def list_policies() -> List[dict]:
    return [
        {
            "name": p.name,
            "description": p.description,
            "block_score_threshold": p.block_score_threshold,
            "escalate_score_threshold": p.escalate_score_threshold,
            "redact_score_threshold": p.redact_score_threshold,
        }
        for p in POLICIES.values()
    ]
