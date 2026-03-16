"""
AEGIS — AI Governance Proxy Hub
FastAPI backend: proxy + governance + audit API
"""
import json
import os
import time
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, Dict, List, Optional

import httpx
from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from database import Base, engine, get_db
from governance import evaluate
from models import AuditDecision
from policies import list_policies
from seed import seed


# ---------------------------------------------------------------------------
# Startup / lifespan
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    seed(260)
    yield


app = FastAPI(
    title="AEGIS — AI Governance Proxy Hub",
    version="1.0.0",
    description="Production-ready AI governance proxy with PII detection, policy enforcement, and audit logging.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPSTREAM_URL = os.environ.get("UPSTREAM_URL", "https://api.openai.com")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")


# ---------------------------------------------------------------------------
# Request / Response schemas
# ---------------------------------------------------------------------------
class ChatMessage(BaseModel):
    role: str
    content: str


class ChatCompletionRequest(BaseModel):
    model: str = "gpt-3.5-turbo"
    messages: List[ChatMessage]
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = None
    stream: Optional[bool] = False
    # AEGIS extensions
    department: Optional[str] = Field(default="Default", alias="x_department")
    user_id: Optional[str] = Field(default=None, alias="x_user_id")

    class Config:
        populate_by_name = True


class AnalyzeRequest(BaseModel):
    prompt: str
    department: Optional[str] = "Default"
    user_id: Optional[str] = None
    model: Optional[str] = None


class EntityOut(BaseModel):
    entity_type: str
    category: str
    value_masked: str
    confidence: float


class DecisionReceiptOut(BaseModel):
    request_id: str
    timestamp: str
    department: str
    user_id: Optional[str]
    model: Optional[str]
    prompt_preview: Optional[str]
    decision: str
    risk_score: float
    detected_entities: List[EntityOut]
    policy_matches: List[str]
    remediation: List[str]
    explanation: str
    latency_ms: Optional[int]
    tokens_input: Optional[int]
    tokens_output: Optional[int]
    upstream_model: Optional[str]


def _record_to_receipt(r: AuditDecision) -> DecisionReceiptOut:
    return DecisionReceiptOut(
        request_id=r.request_id,
        timestamp=r.timestamp.isoformat() if r.timestamp else "",
        department=r.department,
        user_id=r.user_id,
        model=r.model,
        prompt_preview=r.prompt_preview,
        decision=r.decision,
        risk_score=r.risk_score,
        detected_entities=[EntityOut(**e) for e in r.detected_entities],
        policy_matches=r.policy_matches,
        remediation=r.remediation,
        explanation=r.explanation or "",
        latency_ms=r.latency_ms,
        tokens_input=r.tokens_input,
        tokens_output=r.tokens_output,
        upstream_model=r.upstream_model,
    )


# ---------------------------------------------------------------------------
# OpenAI-compatible proxy endpoint
# ---------------------------------------------------------------------------
@app.post("/v1/chat/completions")
async def proxy_chat(
    request: ChatCompletionRequest,
    db: Session = Depends(get_db),
    x_department: Optional[str] = Query(default=None),
    x_user_id: Optional[str] = Query(default=None),
):
    department = x_department or request.department or "Default"
    user_id = x_user_id or request.user_id

    # Extract the full prompt text for analysis
    prompt_text = " ".join(
        msg.content for msg in request.messages if msg.role in ("user", "system")
    )

    t_start = time.time()
    result = evaluate(prompt_text, department=department, user_id=user_id, model=request.model)
    latency_ms = int((time.time() - t_start) * 1000)

    # Determine which prompt to use (possibly redacted)
    effective_prompt = result.redacted_prompt or prompt_text

    tokens_input = len(prompt_text.split())
    tokens_output = 0
    upstream_model = None
    upstream_response = None

    if result.decision == "APPROVE":
        # Forward to upstream
        api_key = OPENAI_API_KEY
        if api_key:
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    payload = request.model_dump(exclude={"department", "user_id"}, by_alias=False)
                    payload.pop("x_department", None)
                    payload.pop("x_user_id", None)
                    resp = await client.post(
                        f"{UPSTREAM_URL}/v1/chat/completions",
                        json=payload,
                        headers={"Authorization": f"Bearer {api_key}"},
                    )
                    if resp.status_code == 200:
                        upstream_response = resp.json()
                        tokens_output = upstream_response.get("usage", {}).get("completion_tokens", 0)
                        upstream_model = upstream_response.get("model")
            except Exception:
                pass

    elif result.decision == "REDACT":
        # Forward with redacted prompt
        if OPENAI_API_KEY:
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    modified_messages = []
                    for msg in request.messages:
                        if msg.role in ("user", "system"):
                            modified_messages.append({"role": msg.role, "content": result.redacted_prompt or msg.content})
                        else:
                            modified_messages.append({"role": msg.role, "content": msg.content})
                    payload = request.model_dump(exclude={"department", "user_id"}, by_alias=False)
                    payload["messages"] = modified_messages
                    resp = await client.post(
                        f"{UPSTREAM_URL}/v1/chat/completions",
                        json=payload,
                        headers={"Authorization": f"Bearer {OPENAI_API_KEY}"},
                    )
                    if resp.status_code == 200:
                        upstream_response = resp.json()
                        tokens_output = upstream_response.get("usage", {}).get("completion_tokens", 0)
                        upstream_model = upstream_response.get("model")
            except Exception:
                pass

    # Save audit record
    preview = prompt_text[:200]
    record = AuditDecision(
        request_id=result.request_id,
        timestamp=result.timestamp,
        department=department,
        user_id=user_id,
        model=request.model,
        prompt_preview=preview,
        decision=result.decision,
        risk_score=result.risk_score,
        detected_entities_json=json.dumps([
            {"entity_type": e.entity_type, "category": e.category,
             "value_masked": e.value_masked, "confidence": e.confidence}
            for e in result.entities
        ]),
        policy_matches_json=json.dumps(result.policy_matches),
        remediation_json=json.dumps(result.remediation),
        explanation=result.explanation,
        latency_ms=latency_ms,
        tokens_input=tokens_input,
        tokens_output=tokens_output,
        upstream_model=upstream_model,
        is_demo=False,
    )
    db.add(record)
    db.commit()

    # Build response
    governance_receipt = {
        "request_id": result.request_id,
        "decision": result.decision,
        "risk_score": result.risk_score,
        "policy": department,
        "entities_detected": len(result.entities),
        "explanation": result.explanation,
    }

    if result.decision in ("BLOCK", "ESCALATE"):
        return {
            "id": f"aegis-{result.request_id}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": request.model,
            "choices": [{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": (
                        f"[AEGIS GOVERNANCE] Request {result.decision}ED. "
                        f"{result.explanation} "
                        f"Remediation: {' '.join(result.remediation)}"
                    ),
                },
                "finish_reason": "content_filter",
            }],
            "usage": {"prompt_tokens": tokens_input, "completion_tokens": 0, "total_tokens": tokens_input},
            "aegis": governance_receipt,
        }

    if upstream_response:
        upstream_response["aegis"] = governance_receipt
        return upstream_response

    # No upstream key or upstream failed — return governance-only response
    return {
        "id": f"aegis-{result.request_id}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": request.model,
        "choices": [{
            "index": 0,
            "message": {
                "role": "assistant",
                "content": f"[AEGIS] Request processed. Decision: {result.decision}. No upstream configured.",
            },
            "finish_reason": "stop",
        }],
        "usage": {"prompt_tokens": tokens_input, "completion_tokens": 0, "total_tokens": tokens_input},
        "aegis": governance_receipt,
    }


# ---------------------------------------------------------------------------
# Analyze endpoint (sandbox)
# ---------------------------------------------------------------------------
@app.post("/api/analyze")
async def analyze_prompt(req: AnalyzeRequest, db: Session = Depends(get_db)):
    t_start = time.time()
    result = evaluate(req.prompt, department=req.department or "Default",
                      user_id=req.user_id, model=req.model)
    latency_ms = int((time.time() - t_start) * 1000)

    preview = req.prompt[:200]
    record = AuditDecision(
        request_id=result.request_id,
        timestamp=result.timestamp,
        department=req.department or "Default",
        user_id=req.user_id,
        model=req.model,
        prompt_preview=preview,
        decision=result.decision,
        risk_score=result.risk_score,
        detected_entities_json=json.dumps([
            {"entity_type": e.entity_type, "category": e.category,
             "value_masked": e.value_masked, "confidence": e.confidence}
            for e in result.entities
        ]),
        policy_matches_json=json.dumps(result.policy_matches),
        remediation_json=json.dumps(result.remediation),
        explanation=result.explanation,
        latency_ms=latency_ms,
        tokens_input=len(req.prompt.split()),
        tokens_output=0,
        upstream_model=None,
        is_demo=False,
    )
    db.add(record)
    db.commit()

    return {
        "request_id": result.request_id,
        "decision": result.decision,
        "risk_score": result.risk_score,
        "entities": [
            {"entity_type": e.entity_type, "category": e.category,
             "value_masked": e.value_masked, "confidence": e.confidence}
            for e in result.entities
        ],
        "policy_matches": result.policy_matches,
        "remediation": result.remediation,
        "explanation": result.explanation,
        "redacted_prompt": result.redacted_prompt,
        "latency_ms": latency_ms,
    }


# ---------------------------------------------------------------------------
# Dashboard API
# ---------------------------------------------------------------------------
@app.get("/api/decisions", response_model=List[DecisionReceiptOut])
def list_decisions(
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
    department: Optional[str] = None,
    decision: Optional[str] = None,
    db: Session = Depends(get_db),
):
    q = db.query(AuditDecision).order_by(desc(AuditDecision.timestamp))
    if department:
        q = q.filter(AuditDecision.department == department)
    if decision:
        q = q.filter(AuditDecision.decision == decision)
    records = q.offset(offset).limit(limit).all()
    return [_record_to_receipt(r) for r in records]


@app.get("/api/decisions/{request_id}", response_model=DecisionReceiptOut)
def get_decision(request_id: str, db: Session = Depends(get_db)):
    record = db.query(AuditDecision).filter(
        AuditDecision.request_id == request_id
    ).first()
    if not record:
        raise HTTPException(status_code=404, detail="Decision not found")
    return _record_to_receipt(record)


@app.get("/api/stats")
def get_stats(db: Session = Depends(get_db)):
    total = db.query(func.count(AuditDecision.id)).scalar() or 0

    decision_counts = (
        db.query(AuditDecision.decision, func.count(AuditDecision.id))
        .group_by(AuditDecision.decision)
        .all()
    )
    by_decision = {d: c for d, c in decision_counts}

    dept_counts = (
        db.query(AuditDecision.department, func.count(AuditDecision.id))
        .group_by(AuditDecision.department)
        .all()
    )
    by_department = {d: c for d, c in dept_counts}

    avg_risk = db.query(func.avg(AuditDecision.risk_score)).scalar() or 0.0

    avg_latency = db.query(func.avg(AuditDecision.latency_ms)).scalar() or 0.0

    # Recent decisions (last 10)
    recent = db.query(AuditDecision).order_by(desc(AuditDecision.timestamp)).limit(10).all()

    # Top entity types
    entity_counts: Dict[str, int] = {}
    all_entities_records = db.query(AuditDecision.detected_entities_json).all()
    for (ej,) in all_entities_records:
        if ej:
            try:
                for ent in json.loads(ej):
                    t = ent.get("entity_type", "UNKNOWN")
                    entity_counts[t] = entity_counts.get(t, 0) + 1
            except Exception:
                pass

    top_entities = sorted(entity_counts.items(), key=lambda x: x[1], reverse=True)[:10]

    return {
        "total_requests": total,
        "by_decision": by_decision,
        "by_department": by_department,
        "avg_risk_score": round(float(avg_risk), 3),
        "avg_latency_ms": round(float(avg_latency), 1),
        "top_entity_types": [{"type": t, "count": c} for t, c in top_entities],
        "recent_decisions": [_record_to_receipt(r) for r in recent],
    }


@app.get("/api/policies")
def get_policies():
    return list_policies()


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "AEGIS", "version": "1.0.0"}


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
