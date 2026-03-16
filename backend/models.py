import json
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, Boolean
from database import Base


class AuditDecision(Base):
    __tablename__ = "audit_decisions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    request_id = Column(String(64), unique=True, index=True, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    department = Column(String(32), index=True, nullable=False)
    user_id = Column(String(64), nullable=True)
    model = Column(String(64), nullable=True)
    prompt_preview = Column(Text, nullable=True)  # first 200 chars, redacted
    decision = Column(String(16), nullable=False)  # APPROVE / REDACT / BLOCK / ESCALATE
    risk_score = Column(Float, nullable=False, default=0.0)
    detected_entities_json = Column(Text, nullable=True)  # JSON list
    policy_matches_json = Column(Text, nullable=True)    # JSON list
    remediation_json = Column(Text, nullable=True)       # JSON list
    explanation = Column(Text, nullable=True)
    latency_ms = Column(Integer, nullable=True)
    tokens_input = Column(Integer, nullable=True)
    tokens_output = Column(Integer, nullable=True)
    upstream_model = Column(String(64), nullable=True)
    is_demo = Column(Boolean, default=False)

    @property
    def detected_entities(self):
        if self.detected_entities_json:
            return json.loads(self.detected_entities_json)
        return []

    @property
    def policy_matches(self):
        if self.policy_matches_json:
            return json.loads(self.policy_matches_json)
        return []

    @property
    def remediation(self):
        if self.remediation_json:
            return json.loads(self.remediation_json)
        return []
