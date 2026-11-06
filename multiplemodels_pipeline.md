# Multi-Model Pipeline — Changelog

Running log of every change made for the multi-model pipeline, newest first.
Started: 2026-10-30.

## What the pipeline does

```
question
   │
   ▼
1. RAG retrieval (ONCE) — embed question → workspace-scoped vector + English lexical search
   → rank fusion, page diversity and same-page context expansion. Workspace filter is mandatory;
   no cross-workspace retrieval can occur through this path.
   │
   ▼
2. Fan out — N local models each answer INDEPENDENTLY from the same
   numbered evidence block, selecting primary/secondary source paragraph IDs.
   Models run concurrently (asyncio.gather); one failing model never
   kills the others (its answer is recorded with an error).
   │
   ▼
3. Agreement scoring — deterministic pairwise Jaccard token overlap
   between answers. No model judges another model; the number is reproducible.
   │
   ▼
4. Source-backed combination — by default, revalidate and deduplicate the
   model-selected excerpts without rewriting them. An explicitly requested
   synthesizer may instead select source spans through constrained JSON.
   │
   ▼
5. Verification — bind each excerpt to its cited source and directly match
   the text. Other claims use bounded judge calls. Source support is not
   a probability of answer correctness or completeness.
```

Sovereign mode is untouched: all models go through `models_client`, which
refuses non-local endpoints when `AI_ALLOW_CLOUD=false`.

## Changes

### 2026-11-04 — v5 combined QA repair and PostgreSQL validation

- Current combined score: 17/20 (85%) original PDF questions through real PostgreSQL retrieval; 9/10 additional PDF questions; 8/8 maintenance-document regressions. These are small, unblinded cohorts, not general accuracy claims. See `research_documents/Combined_QA_Validation_2026-11-04.pdf` for failures and retained transcripts.
- Added English stemming consistently across lexical ranking and SQL, page diversity, and context neighbors within four chunk indices on the same document/page.
- Preserve paragraph qualifiers, render candidates by relevance, label numeric table rows and filter clearly mismatched single-condition numeric rows.
- Use fixed primary/secondary selection fields and an 80-token budget. Missing requested attributes abstain; truncated selections fail closed. Both models' valid excerpts are combined without a third generation call.
- Forward `AI_MULTI_MODELS` through Compose; local configuration uses both tested aliases. Built and checked the AI image, and passed 57 service tests plus real SQL isolation/context checks. Full deployed authentication/upload lifecycle remains untested. Existing PDFs require reingestion.


### 2026-11-04 — live two-model test and grounding fixes

- Tested existing MiniCPM5 1B and Gemma 4 E4B (7.5B total per LM Studio) on `Research_Paper.pdf`, using 20 fixed development questions and retained per-question review rationales.
- Preserved PDF table layout and aligned chunk overlap to line/word boundaries. Previously indexed PDFs need reingestion.
- Added a workspace-filtered lexical candidate channel and vector/BM25 rank fusion to the multi-model retrieval path. Cosine similarity is not replaced by the fused rank. The live pilot used an in-memory index; database SQL execution remains a separate integration check.
- Multi-model generators now select explicit E span IDs through constrained JSON. Source text and citations are rendered by code; fabricated excerpts and truncated responses are rejected.
- Default combination is a revalidated, deduplicated union of model-selected excerpts (`synthesizer=source_union`). An explicitly requested synthesizer remains available as constrained source-span selection. It cannot freely rewrite facts.
- Verification binds claims to cited passages, directly matches exact excerpts, and bounds other checks to 64 tokens / 15 seconds with strict verdict parsing. Model failures cannot seed an invented synthesis.
- UI labels source matching and lexical overlap separately from correctness.
- 49 unit/fake-endpoint integration tests pass; frontend build passes. On this assistant-reviewed development set the combined output moved from 6/20 to 13/20; seven cases remain incomplete or irrelevant. Baseline had one connection failure; the final combined path completed all 20 requests. No production-readiness or general-accuracy claim follows.
- Detailed report: `research_documents/LM_Studio_Document_Test_2026-11-04.pdf`. Raw runs and failed intermediate attempts are retained in `tests/evaluation/results/`.

### 2026-10-30 — session 2: Go route, web UI, integration tests

**New: `apps/api/internal/ask/multi_model.go`**
- `MultiModelHandler` exposing `POST /api/v1/workspaces/:wsId/ask/multi-model`
  (member role required, same as ask). Validates question + max 6 models,
  forwards to the AI service with the workspace scope from the route param,
  writes an `ask.multi_model_completed` audit event with models used.

**Changed: `apps/api/cmd/api/main.go`**
- Registered the multi-model handler on the protected group.

**Changed: `apps/web/src/api.ts`**
- `MultiModelResult` / `MultiModelAnswer` types, `api.multiModel()` call.

**Changed: `apps/web/src/Workbench.tsx`**
- "multi-model mode" checkbox next to the ask box (button becomes "Ask all models").
- New `MultiModelView`: combined answer with verification badge and evidence
  first, agreement panel (pairwise overlaps + mean), then collapsible
  per-model answers with latency, citations, and errors.

**New: `services/ai/tests/integration/test_multi_model.py`** — 4 integration
  tests against a fake OpenAI-compatible endpoint (no real model server, no
  postgres needed — retrieval is stubbed; workspace scoping stays covered by
  the unit suite):
  - missing internal secret is rejected
  - no evidence → refusal, no models called
  - two models fan out over the same evidence, citations map back, agreement
    computed, merged answer verified
  - one model failing (HTTP 500) does not kill the run

**Bug found and fixed during integration testing**
- `MultiModelRequest` was defined inside `register_internal()`; FastAPI could
  not resolve the nested class and treated the body as a query param (422 on
  every call). Moved to module level in `internal_api.py`.

Test results: unit 6/6 multi-model (31/32 suite, 1 pre-existing python-docx
failure), integration 4/4, `go build` + `go vet` + `go test` clean, web
`tsc` + vite build clean.

### 2026-10-30 — initial pipeline

**New: `services/ai/app/multi_model.py`** (~230 lines)
- `retrieve()` — single RAG retrieval, workspace-scoped, focused evidence.
- `answer_with_model()` — one model answers from the shared evidence block.
- `agreement_matrix()` / `jaccard()` — deterministic pairwise overlap stats.
- `extract_citations()` — maps `[n]` markers back to `filename, location`.
- `synthesize()` — merges individual answers into one cited answer.
- `verify_combined()` — reuses `app.grounding.verifier` on the merged answer.
- `run_multi_model_pipeline()` — orchestrates the five stages above.
- `resolve_models()` — model selection order: explicit request →
  `AI_MULTI_MODELS` env (comma-separated, max 6) → active answerer.

**Changed: `services/ai/app/config.py`**
- Added `ai_multi_models: str = ""` setting (comma-separated model ids).

**Changed: `services/ai/app/internal_api.py`**
- New endpoint `POST /internal/query/multi-model` (internal-secret protected,
  same as the rest of the internal API). Request: `{workspace_id, question,
  models?, synthesizer?}`. Response: individual answers with citations and
  latency, agreement matrix, combined answer, verification, evidence.

**New: `services/ai/tests/unit/test_multi_model.py`** — 6 unit tests:
- model resolution (explicit / env / default)
- Jaccard identical + disjoint
- agreement matrix (failed/empty models excluded from pairs)
- citation extraction (valid mapped, out-of-range ignored)

Test results: 6/6 pass. Full unit suite: 31 pass, 1 pre-existing failure
(`test_extraction.py` needs `python-docx` in a fresh venv — unrelated).

### Bugs caught and fixed during testing
- `extract_citations` originally took `n_evidence: int` but referenced an
  undefined `evidence` name — signature changed to take the evidence list.
- `agreement_matrix` counted models with empty answers (no error) as
  "answered" — now requires non-empty answer text.

## How to use

```bash
# env: pick the fan-out models (optional; defaults to the active answerer)
AI_MULTI_MODELS=llama3.2,qwen2.5,mistral

# call (from the Go control plane or directly with the internal secret):
curl -s localhost:8000/internal/query/multi-model \
  -H "X-Internal-Secret: $INTERNAL_API_SECRET" \
  -H 'Content-Type: application/json' \
  -d '{"workspace_id":"<ws>","question":"What causes over-temperature shutdowns?"}'
```

## Not done yet (next steps)
- [x] Go control-plane route + web UI panel to call the new endpoint
- [ ] Persist multi-model runs (agreement stats) for the audit trail
      (audit event written; full run persistence in task_steps still open)
- [x] Integration test against a (fake) model endpoint — real-model smoke
      test still pending a running LM Studio/Ollama endpoint
- [ ] Optionally feed the combined answer through the task/approval flow
