"""Proxy forwarder — forwards (possibly transformed) requests to target LLMs."""

import time
import uuid

import httpx

from config import settings


def mock_llm_response(messages: list[dict], model: str) -> dict:
    """Return a realistic-looking mock response for demo purposes.

    Produces keyword-aware replies so the demo feels intelligent even when no
    real API key is configured.
    """
    prompt_text = " ".join(
        m.get("content", "") for m in messages if isinstance(m.get("content"), str)
    ).lower()

    # Keyword → reply mapping (checked in order)
    keyword_replies: list[tuple[str, str]] = [
        (
            "hello",
            "Hello! I'm AEGIS, your AI governance proxy. How can I help you today?",
        ),
        (
            "hi",
            "Hi there! I'm running in demo mode. Your prompt was safely processed by AEGIS.",
        ),
        (
            "pii",
            (
                "PII (Personally Identifiable Information) refers to data that can identify "
                "an individual, such as names, email addresses, phone numbers, or social "
                "security numbers. AEGIS automatically detects and redacts such data before "
                "forwarding requests to the LLM."
            ),
        ),
        (
            "privacy",
            (
                "Privacy protection is at the core of AEGIS. All prompts are scanned for "
                "sensitive data before they reach the underlying model, and a full audit "
                "trail is maintained for compliance purposes."
            ),
        ),
        (
            "security",
            (
                "AEGIS provides enterprise-grade security for your LLM interactions by "
                "intercepting, inspecting, and governing all traffic through a policy-driven "
                "proxy layer."
            ),
        ),
        (
            "redact",
            (
                "Redaction in AEGIS uses a hybrid approach: regex patterns catch "
                "structured PII (emails, phone numbers, credit card numbers), while a "
                "named-entity recognition model identifies unstructured sensitive data such "
                "as person names and organisations."
            ),
        ),
        (
            "explain",
            (
                "I'm happy to explain! AEGIS acts as a transparent proxy between your "
                "application and the target LLM. It detects sensitive data, applies your "
                "organisation's policies, optionally redacts content, and then forwards the "
                "sanitised prompt — all in real time."
            ),
        ),
        (
            "help",
            (
                "I'm here to help. AEGIS is currently running in demo mode (no API key "
                "configured). You can explore the governance features without needing a live "
                "LLM connection. Ask me about PII detection, redaction, policies, or security."
            ),
        ),
    ]

    reply = next(
        (reply for keyword, reply in keyword_replies if keyword in prompt_text),
        (
            "I've received your message. AEGIS is running in demo mode — no API key is "
            "configured, so this is a mock response. Your prompt was processed through the "
            "full governance pipeline (detection → decision → policy) before reaching this "
            "point."
        ),
    )

    prompt_tokens = max(10, sum(len(m.get("content", "").split()) for m in messages))
    completion_tokens = len(reply.split())

    return {
        "id": f"chatcmpl-mock-{uuid.uuid4().hex[:12]}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": model,
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": reply},
                "finish_reason": "stop",
            }
        ],
        "usage": {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens,
        },
        "note": "(Mock response - no API key configured)",
    }


async def forward_to_llm(
    model: str,
    messages: list[dict],
    temperature: float = 0.7,
    max_tokens: int = 1024,
) -> dict:
    """Forward sanitised messages to the target LLM and return the parsed response.

    Falls back to :func:`mock_llm_response` when no API key is available.
    Returns a structured error dict when the upstream call fails or times out.
    """
    api_key = settings.openai_api_key
    base_url = settings.target_llm_base_url.rstrip("/")

    if not api_key:
        return mock_llm_response(messages, model)

    url = f"{base_url}/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            return response.json()
    except httpx.TimeoutException:
        return {
            "error": "timeout",
            "message": "The request to the LLM timed out after 10 seconds.",
            "model": model,
        }
    except httpx.HTTPStatusError as exc:
        return {
            "error": "http_error",
            "status_code": exc.response.status_code,
            "message": str(exc),
            "model": model,
        }
    except httpx.RequestError as exc:
        return {
            "error": "request_error",
            "message": str(exc),
            "model": model,
        }
