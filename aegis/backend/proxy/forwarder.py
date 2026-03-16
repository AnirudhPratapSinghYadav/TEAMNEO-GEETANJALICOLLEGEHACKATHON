"""Proxy forwarder — forwards (possibly transformed) requests to target LLMs."""

from typing import Any, Dict

import httpx

from config import settings

# TODO: implement async request forwarding logic


async def forward(request: Any, prompt: str) -> Dict[str, Any]:
    """Forward *request* (with *prompt* as the final user message) to the target LLM.

    Returns the raw LLM response dict (OpenAI-compatible).
    If the API key is missing or the upstream call fails, returns a mock response so
    the governance pipeline can still be exercised end-to-end.
    """
    if not settings.openai_api_key:
        # No API key configured — return a safe mock response for demo / testing.
        return {
            "id": "mock-llm-response",
            "object": "chat.completion",
            "model": request.model,
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": "[AEGIS Demo] LLM response placeholder — configure OPENAI_API_KEY to enable real forwarding.",
                    },
                    "finish_reason": "stop",
                }
            ],
        }

    # Build the messages list, replacing the last user message with the (possibly redacted) prompt.
    messages = [msg.model_dump() for msg in request.messages]
    for i in range(len(messages) - 1, -1, -1):
        if messages[i]["role"] == "user":
            messages[i]["content"] = prompt
            break

    payload: Dict[str, Any] = {"model": request.model, "messages": messages}
    if request.temperature is not None:
        payload["temperature"] = request.temperature
    if request.max_tokens is not None:
        payload["max_tokens"] = request.max_tokens

    headers = {
        "Authorization": f"Bearer {settings.openai_api_key}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.post(
                f"{settings.target_llm_base_url}/chat/completions",
                json=payload,
                headers=headers,
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as exc:
            # Upstream API returned an error status — return a graceful error message.
            return {
                "id": "upstream-error",
                "object": "chat.completion",
                "model": request.model,
                "choices": [
                    {
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": f"[AEGIS] Upstream LLM error ({exc.response.status_code}): {exc.response.text[:200]}",
                        },
                        "finish_reason": "stop",
                    }
                ],
            }
        except httpx.RequestError as exc:
            # Network-level failure — return a graceful error message.
            return {
                "id": "network-error",
                "object": "chat.completion",
                "model": request.model,
                "choices": [
                    {
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": f"[AEGIS] Failed to reach upstream LLM: {exc}",
                        },
                        "finish_reason": "stop",
                    }
                ],
            }
