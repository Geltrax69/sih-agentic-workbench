"""Model adapter: OpenAI-compatible local endpoint (Ollama/vLLM/LM Studio).

Sovereign mode is enforced by config validation (see config.py); this module
additionally refuses to call non-local endpoints when AI_ALLOW_CLOUD is false.
"""

from __future__ import annotations

import httpx

from app.config import settings

Embedder = list[list[float]]


class ModelError(Exception):
    pass


def _local_client(timeout: float = 60.0) -> httpx.AsyncClient:
    if not settings.ai_allow_cloud and not settings.is_local_endpoint:
        raise ModelError(
            f"sovereign mode: refusing to call non-local endpoint {settings.ai_base_url}"
        )
    return httpx.AsyncClient(timeout=timeout)


async def embed(texts: list[str]) -> Embedder:
    """Embed texts via the OpenAI-compatible /v1/embeddings endpoint."""
    if not texts:
        return []
    async with _local_client() as client:
        resp = await client.post(
            f"{settings.ai_base_url}/embeddings",
            json={"model": settings.ai_embedding_model, "input": texts},
        )
    if resp.status_code != 200:
        raise ModelError(f"embedding failed: HTTP {resp.status_code}: {resp.text[:200]}")
    data = resp.json()
    ordered = sorted(data["data"], key=lambda d: d["index"])
    return [item["embedding"] for item in ordered]


async def generate(
    prompt: str,
    system: str | None = None,
    max_tokens: int = 1024,
    model: str | None = None,
    temperature: float = 0.3,
    reasoning_effort: str | None = None,
    response_schema: dict | None = None,
) -> str:
    """One-shot completion via /v1/chat/completions."""
    messages: list[dict] = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    body = {
        "model": model or settings.ai_model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    effort = settings.ai_reasoning_effort if reasoning_effort is None else reasoning_effort
    if effort:
        body["reasoning_effort"] = effort
    if response_schema is not None:
        body["response_format"] = {"type": "json_schema", "json_schema": {
            "name": "source_excerpts", "strict": True, "schema": response_schema,
        }}
    async with _local_client(timeout=120.0) as client:
        resp = await client.post(f"{settings.ai_base_url}/chat/completions", json=body)
    if resp.status_code != 200:
        raise ModelError(f"generation failed: HTTP {resp.status_code}: {resp.text[:200]}")
    msg = resp.json()["choices"][0]["message"]
    if resp.json()["choices"][0].get("finish_reason") == "length":
        raise ModelError("generation exceeded its output-token budget")
    return (msg.get("content") or "").strip()


async def list_models() -> list[dict]:
    """Models the local endpoint can serve: [{id, type: llm|embeddings, state}].

    LM Studio's /api/v0/models lists every downloaded model with type and load
    state; other OpenAI-compatible servers (Ollama, vLLM) only have /v1/models,
    so type is guessed from the name there and state is unknown.
    """
    root = settings.ai_base_url.rstrip("/").removesuffix("/v1")
    async with _local_client(timeout=10.0) as client:
        resp = await client.get(f"{root}/api/v0/models")
        if resp.status_code != 200:
            resp = await client.get(f"{settings.ai_base_url}/models")
    if resp.status_code != 200:
        raise ModelError(f"listing models failed: HTTP {resp.status_code}: {resp.text[:200]}")
    return [
        {
            "id": m["id"],
            "type": m.get("type") or ("embeddings" if "embed" in m["id"].lower() else "llm"),
            "state": m.get("state", ""),
        }
        for m in resp.json().get("data", [])
    ]


async def warm_up(model: str) -> None:
    """One-token request: makes LM Studio (JIT) load the model now, and proves it answers."""
    async with _local_client(timeout=300.0) as client:
        resp = await client.post(
            f"{settings.ai_base_url}/chat/completions",
            json={"model": model, "messages": [{"role": "user", "content": "hi"}], "max_tokens": 1},
        )
    if resp.status_code != 200:
        raise ModelError(f"model {model} failed to load: HTTP {resp.status_code}: {resp.text[:200]}")
