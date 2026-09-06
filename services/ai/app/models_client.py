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


async def generate(prompt: str, system: str | None = None, max_tokens: int = 1024) -> str:
    """One-shot completion via /v1/chat/completions."""
    messages: list[dict] = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    async with _local_client(timeout=120.0) as client:
        resp = await client.post(
            f"{settings.ai_base_url}/chat/completions",
            json={
                "model": settings.ai_model,
                "messages": messages,
                "temperature": 0.3,
                "max_tokens": max_tokens,
            },
        )
    if resp.status_code != 200:
        raise ModelError(f"generation failed: HTTP {resp.status_code}: {resp.text[:200]}")
    msg = resp.json()["choices"][0]["message"]
    return (msg.get("content") or "").strip()
