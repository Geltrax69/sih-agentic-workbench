"""Multi-model pipeline: one RAG retrieval, N local models answer independently,
then a deterministic agreement pass and a synthesizer merge into one cited answer.

Design (matches docs/architecture.md invariants):
- Retrieval happens ONCE and is workspace-scoped (search_workspace enforces it).
- Every model sees the SAME evidence block, quoted as untrusted data.
- Models run against the same local OpenAI-compatible endpoint (sovereign mode
  is enforced in models_client; nothing here can reach a cloud host).
- Model output can never elevate permissions: this module only reads.
"""

from __future__ import annotations

import asyncio
import json
import re
import time
from dataclasses import dataclass, field

from app import models_client
from app.config import settings
from app.grounding import excerpts
from app.ingestion import search_workspace
from app.orchestration.executor import cite
from app.retrieval import expand_context, select_evidence


@dataclass
class ModelAnswer:
    model: str
    answer: str
    citations: list[str] = field(default_factory=list)
    latency_ms: int = 0
    error: str = ""


@dataclass
class MultiModelResult:
    question: str
    evidence: list[dict]
    answers: list[ModelAnswer]
    agreement: dict            # deterministic pairwise overlap stats
    combined_answer: str
    synthesizer: str
    verification: dict = field(default_factory=dict)


def resolve_models(requested: list[str] | None = None) -> list[str]:
    """Models to fan out to: explicit request > AI_MULTI_MODELS env > active answerer."""
    if requested:
        return requested[:6]
    env = (settings.ai_multi_models or "").strip()
    if env:
        return [m.strip() for m in env.split(",") if m.strip()][:6]
    return [settings.ai_model]


async def retrieve(workspace_id: str, question: str, limit: int = 8) -> list[dict]:
    """RAG step: embed the question, workspace-scoped vector search, focus top hits."""
    vectors = await models_client.embed([question])
    rows = search_workspace(settings.database_url, workspace_id, vectors[0], max(limit, 16), question=question)
    candidates = [
            {
                "chunk_id": str(r["id"]),
                "document_id": str(r["document_id"]),
                "filename": r["filename"],
                "chunk_index": r["chunk_index"],
                "location": r["location"],
                "content": r["content"],
                "score": float(r["score"]),
                "context_only": r.get("context_only", False),
            }
            for r in rows
        ]
    return expand_context(select_evidence(question, candidates), candidates)


def evidence_block(evidence: list[dict]) -> str:
    return "\n\n".join(
        f"[{i + 1}] ({cite(e)})\n{excerpts.source_text(e['content'])}" for i, e in enumerate(evidence)
    )


_CITE_RE = re.compile(r"\[(\d+)\]")


def extract_citations(answer: str, evidence: list[dict]) -> list[str]:
    """Map [n] markers in an answer back to 'filename, location' strings."""
    seen: list[int] = []
    for m in _CITE_RE.finditer(answer):
        n = int(m.group(1))
        if 1 <= n <= len(evidence) and n not in seen:
            seen.append(n)
    return [cite(evidence[n - 1]) for n in seen]


_STOP = {"the", "a", "an", "is", "are", "was", "were", "of", "to", "in", "and",
         "or", "for", "on", "with", "at", "by", "from", "that", "this", "it",
         "as", "be", "not", "which", "when", "if", "no", "so", "do", "does"}


def _tokens(text: str) -> set[str]:
    words = re.findall(r"[a-z0-9]+", text.lower())
    return {w for w in words if w not in _STOP and len(w) > 2}


def jaccard(a: str, b: str) -> float:
    ta, tb = _tokens(a), _tokens(b)
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


def agreement_matrix(answers: list[ModelAnswer]) -> dict:
    """Deterministic pairwise content overlap. No model judges another model."""
    ok = [a for a in answers if not a.error and a.answer]
    pairs = []
    for i in range(len(ok)):
        for j in range(i + 1, len(ok)):
            pairs.append(
                {
                    "a": ok[i].model,
                    "b": ok[j].model,
                    "overlap": round(jaccard(ok[i].answer, ok[j].answer), 3),
                }
            )
    mean = round(sum(p["overlap"] for p in pairs) / len(pairs), 3) if pairs else 0.0
    return {"pairs": pairs, "mean_overlap": mean, "n_answered": len(ok)}


async def answer_with_model(model: str, block: str, question: str) -> ModelAnswer:
    """One model answers independently from the shared evidence block."""
    start = time.monotonic()
    try:
        if not excerpts.candidate_ids(block, question):
            return ModelAnswer(model=model, answer=excerpts.REFUSAL)
        text = await models_client.generate(
            excerpts.selection_prompt(block, question), model=model, max_tokens=80,
            temperature=0.0, reasoning_effort="none", response_schema=excerpts.selection_schema(block, question),
        )
        return ModelAnswer(model=model, answer=excerpts.render_selection(text, block, question), latency_ms=int((time.monotonic() - start) * 1000))
    except Exception as exc:  # noqa: BLE001 — one bad model must not kill the others
        return ModelAnswer(model=model, answer="", error=str(exc)[:200],
                           latency_ms=int((time.monotonic() - start) * 1000))


async def synthesize(
    synthesizer: str, block: str, question: str, answers: list[ModelAnswer], *, use_model: bool = False,
) -> str:
    candidates = [a for a in answers if not a.error and a.answer and a.answer != excerpts.REFUSAL]
    if not candidates:
        return excerpts.REFUSAL
    if len(candidates) == 1 or len({a.answer for a in candidates}) == 1:
        return candidates[0].answer
    if not use_model:
        # Revalidate and deduplicate the candidate excerpts. No generation can
        # discard a correct candidate or insert a new claim in the default path.
        merged = []
        seen = set()
        for candidate in candidates:
            for line in candidate.answer.splitlines():
                ids = _CITE_RE.findall(line)
                if not ids:
                    raise ValueError("Candidate excerpt has no source citation")
                text = _CITE_RE.sub("", line).strip()
                validated = excerpts.render(json.dumps({"quotes": [{"source": int(ids[-1]), "text": text}]}), block)
                if text not in seen:
                    merged.append(validated)
                    seen.add(text)
        return "\n".join(merged) or excerpts.REFUSAL
    listing = "\n\n".join(f"--- {a.model} ---\n{a.answer}" for a in candidates)
    text = await models_client.generate(
        excerpts.selection_prompt(block, question, listing), model=synthesizer, max_tokens=80,
        temperature=0.0, reasoning_effort="none", response_schema=excerpts.selection_schema(block, question),
    )
    return excerpts.render_selection(text, block, question)


async def run_multi_model_pipeline(
    workspace_id: str,
    question: str,
    models: list[str] | None = None,
    synthesizer: str | None = None,
) -> MultiModelResult:
    """Retrieve once -> fan out -> agreement -> merge -> verify."""
    chosen = resolve_models(models)
    synth = synthesizer or settings.ai_model

    evidence = await retrieve(workspace_id, question)
    if not evidence:
        return MultiModelResult(
            question=question,
            evidence=[],
            answers=[],
            agreement={"pairs": [], "mean_overlap": 0.0, "n_answered": 0},
            combined_answer="I don't know — no relevant evidence was found in this workspace.",
            synthesizer=synth,
        )

    block = evidence_block(evidence)
    answers = await asyncio.gather(*(answer_with_model(m, block, question) for m in chosen))
    for a in answers:
        a.citations = extract_citations(a.answer, evidence)

    agreement = agreement_matrix(list(answers))
    synthesis_error = ""
    try:
        combined = await synthesize(synth, block, question, list(answers), use_model=bool(synthesizer))
    except Exception as exc:
        combined = excerpts.REFUSAL
        synthesis_error = str(exc)[:200]

    result = MultiModelResult(
        question=question,
        evidence=evidence,
        answers=list(answers),
        agreement=agreement,
        combined_answer=combined,
        synthesizer=synth if synthesizer else "source_union",
    )
    result.verification = await verify_combined(block, question, combined, synth)
    if synthesis_error:
        result.verification.update(decision="unverified", confidence=0.0, error=synthesis_error)
    return result


async def verify_combined(block: str, question: str, answer: str, model: str) -> dict:
    """Reuse the existing grounding verifier on the merged answer."""
    from app.grounding import verifier

    try:
        verifier_model = settings.ai_verifier_model or model
        claims = await verifier.verify(block, question, answer)
        confidence, decision = verifier.score(claims, weak_evidence=False)
        return {"model": verifier_model, "claims": claims, "confidence": confidence,
                "decision": decision, "method": "source_excerpt_match" if claims and all(c.get("reason") == "exact excerpt in cited source" for c in claims) else "cited_claim_checks"}
    except Exception as exc:  # noqa: BLE001 — a failed check must not lose the answer
        return {"model": model, "claims": [], "confidence": 0.0,
                "decision": "unverified", "error": str(exc)[:200]}
