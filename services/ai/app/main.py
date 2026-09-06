"""Sovereign Agentic AI Workbench — Python AI service.

Owns ingestion, embeddings, hybrid retrieval, knowledge graph, agent
planning/execution, model adapters and verification. Authorization is
resolved by the Go control plane and passed in with every request.
"""

from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

import httpx
from fastapi import FastAPI

from app.config import settings
from app.internal_api import register_internal


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    problems = settings.validate_sovereign_mode()
    if problems:
        # Logged loudly, but service still boots: healthz reports it degraded.
        for p in problems:
            app.state.sovereign_violations = problems
    yield


app = FastAPI(title="Workbench AI Service", version="0.1.0", lifespan=lifespan)


@app.get("/healthz")
async def healthz() -> dict:
    components: dict[str, dict] = {}

    # Model endpoint — optional: workbench degrades without it.
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            resp = await client.get(f"{settings.ai_base_url}/models")
            components["model_endpoint"] = (
                {"status": "up"} if resp.status_code < 500
                else {"status": "down", "error": f"HTTP {resp.status_code}"}
            )
    except Exception as exc:  # noqa: BLE001 — health must never raise
        components["model_endpoint"] = {"status": "down", "error": str(exc)}

    violations = getattr(app.state, "sovereign_violations", [])
    status = "ok"
    if violations:
        status = "degraded"
        components["sovereign_policy"] = {"status": "violated", "problems": violations}

    return {"status": status, "components": components}


register_internal(app)


@app.get("/api/v1/ai/ping")
async def ping() -> dict:
    return {"service": "ai", "model": settings.ai_model, "provider": settings.ai_provider}
