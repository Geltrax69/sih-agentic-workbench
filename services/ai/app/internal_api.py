"""Internal API surface (Go control plane -> AI service).

Protected by the shared INTERNAL_API_SECRET bearer token. The Go side always
sends an already-resolved workspace scope; this service never derives
permissions itself (ADR-002).
"""

from __future__ import annotations

from typing import Literal

import fastapi
import httpx
from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, Field

from app import ingestion, models_client, multi_model
from app.config import settings
from app.orchestration.executor import Orchestrator, cite, focus_evidence, grounded_prompt


def require_internal(secret_header: str = fastapi.Header(alias="X-Internal-Secret")) -> None:
    if not settings.internal_api_secret or secret_header != settings.internal_api_secret:
        raise HTTPException(status_code=401, detail="invalid internal secret")


class QueryRequest(BaseModel):
    workspace_id: str = Field(min_length=1)
    question: str = Field(min_length=1, max_length=4000)
    limit: int = Field(default=6, ge=1, le=20)


class Evidence(BaseModel):
    chunk_id: str
    document_id: str
    filename: str
    chunk_index: int
    location: str = ""
    content: str
    score: float


class ActiveModelRequest(BaseModel):
    # empty model is only valid for the verifier: "same as the answerer"
    model: str = Field(max_length=200)
    role: Literal["answerer", "verifier"] = "answerer"


# role -> settings attribute, also used as the app_settings key
MODEL_ROLES = {"answerer": "ai_model", "verifier": "ai_verifier_model"}


def save_active_model(role: str, model: str) -> None:
    import psycopg

    key = MODEL_ROLES[role]
    with psycopg.connect(settings.database_url) as conn:
        conn.execute(
            """INSERT INTO app_settings (key, value) VALUES (%s, %s)
               ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value, updated_at = now()""",
            (key, model),
        )
    setattr(settings, key, model)


def load_active_model() -> None:
    """Apply the models chosen in the UI, if any; otherwise keep the env values."""
    import psycopg

    with psycopg.connect(settings.database_url) as conn:
        rows = conn.execute(
            "SELECT key, value FROM app_settings WHERE key = ANY(%s)", (list(MODEL_ROLES.values()),)
        ).fetchall()
    for key, value in rows:
        setattr(settings, key, value)


class QueryResponse(BaseModel):
    answer: str
    evidence: list[Evidence]


class TaskRequest(BaseModel):
    workspace_id: str = Field(min_length=1)
    user_id: str = Field(min_length=1)
    question: str = Field(min_length=1, max_length=4000)


class ApprovalRequest(BaseModel):
    approved: bool
    decided_by: str = Field(min_length=1)


class MultiModelRequest(BaseModel):
    workspace_id: str = Field(min_length=1)
    question: str = Field(min_length=1, max_length=4000)
    models: list[str] = Field(default_factory=list, max_length=6)
    synthesizer: str = Field(default="", max_length=200)


def register_internal(app: FastAPI) -> None:
    pipeline = ingestion.IngestPipeline(settings.database_url)
    orchestrator = Orchestrator(settings.database_url)

    @app.post("/internal/ingest/run", dependencies=[Depends(require_internal)])
    async def run_ingestion() -> dict:
        result = await pipeline.run_pending_one()
        if result is None:
            return {"status": "idle"}
        return {"status": result.status, "document_id": result.document_id, "chunks": result.chunks}

    @app.get("/internal/models", dependencies=[Depends(require_internal)])
    async def list_models() -> dict:
        try:
            models = await models_client.list_models()
        except (models_client.ModelError, httpx.HTTPError) as exc:
            raise HTTPException(status_code=503, detail=f"model endpoint unavailable: {exc}") from exc
        return {"active": settings.ai_model, "verifier": settings.ai_verifier_model, "models": models}

    @app.post("/internal/models/active", dependencies=[Depends(require_internal)])
    async def set_active_model(req: ActiveModelRequest) -> dict:
        if not req.model:
            if req.role == "answerer":
                raise HTTPException(status_code=400, detail="answerer model is required")
            save_active_model(req.role, "")
            return {"active": settings.ai_model, "verifier": ""}
        models = await models_client.list_models()
        match = next((m for m in models if m["id"] == req.model), None)
        if match is None:
            raise HTTPException(status_code=404, detail=f"model not found: {req.model}")
        if match["type"] == "embeddings":
            # the embedding model is fixed: changing it would invalidate every indexed chunk
            raise HTTPException(status_code=400, detail="embedding models cannot be used for chat")
        try:
            await models_client.warm_up(req.model)
        except (models_client.ModelError, httpx.HTTPError) as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc
        save_active_model(req.role, req.model)
        return {"active": settings.ai_model, "verifier": settings.ai_verifier_model}

    @app.post("/internal/tasks", dependencies=[Depends(require_internal)])
    async def start_task(req: TaskRequest) -> dict:
        return await orchestrator.start_task(req.workspace_id, req.user_id, req.question)

    @app.get("/internal/tasks/{task_id}", dependencies=[Depends(require_internal)])
    async def get_task(task_id: str) -> dict:
        return orchestrator.get_task(task_id)

    @app.post("/internal/tasks/{task_id}/approval", dependencies=[Depends(require_internal)])
    async def decide_approval(task_id: str, req: ApprovalRequest) -> dict:
        return await orchestrator.resume_after_approval(task_id, req.approved, req.decided_by)

    @app.post("/internal/query", response_model=QueryResponse, dependencies=[Depends(require_internal)])
    async def query_workspace(req: QueryRequest) -> QueryResponse:
        vectors = await models_client.embed([req.question])
        rows = ingestion.search_workspace(
            settings.database_url, req.workspace_id, vectors[0], req.limit
        )
        evidence = [
            Evidence(
                chunk_id=str(r["id"]),
                document_id=str(r["document_id"]),
                filename=r["filename"],
                chunk_index=r["chunk_index"],
                location=r["location"],
                content=r["content"],
                score=float(r["score"]),
            )
            for r in rows
        ]
        if not evidence:
            return QueryResponse(
                answer="I don't know — no relevant evidence was found in this workspace.",
                evidence=[],
            )

        evidence = [Evidence(**e) for e in focus_evidence([e.model_dump() for e in evidence])]
        evidence_block = "\n\n".join(
            f"[{i + 1}] ({cite(e.model_dump())})\n{e.content}" for i, e in enumerate(evidence)
        )
        prompt = grounded_prompt(evidence_block, req.question)
        answer = await models_client.generate(prompt, max_tokens=800)
        return QueryResponse(answer=answer, evidence=evidence)

    @app.post("/internal/query/multi-model", dependencies=[Depends(require_internal)])
    async def query_multi_model(req: MultiModelRequest) -> dict:
        """One RAG retrieval, N local models answer independently, agreement
        scoring, then a synthesizer merges into one cited answer."""
        try:
            result = await multi_model.run_multi_model_pipeline(
                req.workspace_id, req.question,
                models=req.models or None,
                synthesizer=req.synthesizer or None,
            )
        except (models_client.ModelError, httpx.HTTPError) as exc:
            raise HTTPException(status_code=503, detail=f"model endpoint unavailable: {exc}") from exc
        return {
            "question": result.question,
            "models_used": [a.model for a in result.answers],
            "individual_answers": [
                {"model": a.model, "answer": a.answer, "citations": a.citations,
                 "latency_ms": a.latency_ms, "error": a.error}
                for a in result.answers
            ],
            "agreement": result.agreement,
            "combined_answer": result.combined_answer,
            "synthesizer": result.synthesizer,
            "verification": result.verification,
            "evidence": result.evidence,
        }
