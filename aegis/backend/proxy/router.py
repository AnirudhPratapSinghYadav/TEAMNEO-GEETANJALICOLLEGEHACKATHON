"""Proxy router — routes incoming requests to the appropriate LLM backend."""

import time
import uuid
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel

from decision import engine as decision_engine
from detection import hybrid_detector
from policy import engine as policy_engine
from receipt import generator as receipt_generator
from scoring import risk_scorer
from storage import database

from . import forwarder

router = APIRouter()

# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------


class Message(BaseModel):
    role: str
    content: str


class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[Message]
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    user: Optional[str] = None


class GovernanceMetadata(BaseModel):
    risk_score: float
    decision: str
    entities_detected: List[Dict[str, Any]]
    policies_matched: List[str]
    processing_time_ms: float


class AegisResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    model: str
    choices: List[Dict[str, Any]]
    governance: GovernanceMetadata
    receipt: Dict[str, Any]


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------


def _policy_names(policies: List[Dict[str, Any]]) -> List[str]:
    """Extract a human-readable name from each matched policy dict."""
    return [p.get("name", str(p)) if isinstance(p, dict) else str(p) for p in policies]


@router.post("/v1/chat/completions", response_model=AegisResponse)
async def chat_completions(
    request: ChatCompletionRequest,
    x_aegis_user_id: str = Header(default="user_001", alias="X-Aegis-User-Id"),
    x_aegis_user_name: str = Header(default="Demo User", alias="X-Aegis-User-Name"),
    x_aegis_department: str = Header(default="engineering", alias="X-Aegis-Department"),
) -> AegisResponse:
    """Intercept and govern an LLM chat-completion request through the AEGIS pipeline."""
    start_time = time.monotonic()
    request_id = str(uuid.uuid4())

    try:
        # Build user context that flows through the entire pipeline.
        user_context: Dict[str, Any] = {
            "user_id": x_aegis_user_id,
            "user_name": x_aegis_user_name,
            "department": x_aegis_department,
            "request_id": request_id,
        }

        # Extract the last user message as the prompt to analyse.
        prompt = ""
        for msg in reversed(request.messages):
            if msg.role == "user":
                prompt = msg.content
                break

        if not prompt:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "missing_user_message",
                    "message": "Request must contain at least one message with role 'user'.",
                    "request_id": request_id,
                },
            )

        # ------------------------------------------------------------------
        # Step 1 — PII / credential detection
        # ------------------------------------------------------------------
        entities: List[Dict[str, Any]] = hybrid_detector.detect(prompt, user_context)

        # ------------------------------------------------------------------
        # Step 2 — Policy evaluation
        # ------------------------------------------------------------------
        policies: List[Dict[str, Any]] = policy_engine.evaluate(entities, user_context)

        # ------------------------------------------------------------------
        # Step 3 — Risk scoring
        # ------------------------------------------------------------------
        risk_result: Dict[str, Any] = risk_scorer.calculate(entities, policies, user_context)
        risk_score: float = risk_result.get("score", 0.0)

        # ------------------------------------------------------------------
        # Step 4 — Decision engine
        # ------------------------------------------------------------------
        decision_result: Dict[str, Any] = decision_engine.decide(
            risk_score, entities, policies, user_context
        )
        decision: str = decision_result.get("decision", "APPROVE")

        # ------------------------------------------------------------------
        # Step 5 — Forward to LLM or return block/escalate response
        # ------------------------------------------------------------------
        if decision in ("APPROVE", "REDACT"):
            # Use the redacted prompt when the decision engine performed redaction.
            forward_prompt = decision_result.get("redacted_prompt", prompt)
            llm_response: Dict[str, Any] = await forwarder.forward(request, forward_prompt)
        else:
            # BLOCK or ESCALATE — do not forward; return a governance message.
            block_message: str = decision_result.get(
                "message",
                f"Request blocked by AEGIS governance policy. Decision: {decision}",
            )
            llm_response = {
                "id": request_id,
                "object": "chat.completion",
                "model": request.model,
                "choices": [
                    {
                        "index": 0,
                        "message": {"role": "assistant", "content": block_message},
                        "finish_reason": "stop",
                    }
                ],
            }

        # ------------------------------------------------------------------
        # Step 6 — Measure total processing time
        # ------------------------------------------------------------------
        processing_time_ms: float = (time.monotonic() - start_time) * 1000

        # ------------------------------------------------------------------
        # Step 7 — Generate decision receipt
        # ------------------------------------------------------------------
        receipt: Dict[str, Any] = receipt_generator.generate(
            request_id=request_id,
            user_context=user_context,
            prompt=prompt,
            entities=entities,
            policies=policies,
            risk_result=risk_result,
            decision_result=decision_result,
            processing_time_ms=processing_time_ms,
        )

        # ------------------------------------------------------------------
        # Step 8 — Persist to database
        # ------------------------------------------------------------------
        database.store(
            request_id=request_id,
            user_context=user_context,
            prompt=prompt,
            entities=entities,
            policies=policies,
            risk_result=risk_result,
            decision_result=decision_result,
            receipt=receipt,
        )

        # ------------------------------------------------------------------
        # Build and return the AEGIS response
        # ------------------------------------------------------------------
        governance = GovernanceMetadata(
            risk_score=risk_score,
            decision=decision,
            entities_detected=entities,
            policies_matched=_policy_names(policies),
            processing_time_ms=processing_time_ms,
        )

        return AegisResponse(
            id=request_id,
            model=request.model,
            choices=llm_response.get("choices", []),
            governance=governance,
            receipt=receipt,
        )

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail={
                "error": "governance_pipeline_error",
                "message": str(exc),
                "request_id": request_id,
            },
        ) from exc
