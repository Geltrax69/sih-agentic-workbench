> **Evidence update — 3 November 2026:** This is an earlier draft, not proof of patentability or comparative superiority. Read [Evidence Review](Evidence_Review_2026-11-03.md) before using its novelty, performance, citation, or disclosure claims. RAG Ensemble Section 4.7 already evaluates generators over fixed reference documents. Public-disclosure and inventorship declarations need confirmation.

# Prior Art Research — Multi-Model RAG / LLM Ensembles

Research date: 2026-10-30. Sources: web search (DuckDuckGo), OpenAlex scholarly search,
and the project's own documents (Research_Paper.pdf, SIH_Documentation.pdf).
Every claim below is traceable to the source named with it.

## Question 1: Has anyone made the same thing?

**Updated assessment (3 November 2026): the combination is implemented, but novelty is not established.**

This was a targeted search, not proof that no comparable system exists. RAG Ensemble
Section 4.7 already fixes the reference documents, varies generators and fuses their
answers. The IBM ensemble-QA patent family is also a relevant screening lead. Deployment
controls and lexical-agreement inspection need a narrower claim-level comparison and
measured technical benefit. See the dated Evidence Review and source register.

Closest systems and what each one covers:

### 1. Mixture-of-Agents (MoA) — Wang et al., arXiv:2406.04692 (2024); Together AI implementation
- What they did: layered architecture; each layer has multiple LLM agents, each agent takes ALL
  outputs from the previous layer as auxiliary information. Using only open-source models, MoA
  scored 65.1% on AlpacaEval 2.0 vs GPT-4 Omni's 57.5% (per the paper abstract and the
  togethercomputer/MoA GitHub README).
- What they did NOT do: no retrieval grounding, no citations, no workspace permissions, no audit,
  no on-premise constraint. Layered = sequential and expensive; designed for cloud serving.
- Relation to us: we adopt the "multiple models then aggregate" idea but flatten it to one
  parallel fan-out round sized for a single local endpoint, and we ground every model in the same
  retrieved evidence.

### 2. LLM-Blender — Jiang, Ren & Lin, ACL 2023
- What they did: PairRanker (cross-attention pairwise comparison model) ranks candidate outputs;
  GenFuser merges the top candidates. Showed the best LLM varies per input, so ensembling wins.
- What they did NOT do: requires training the ranker on comparison data; no RAG, no citations, no
  enterprise controls.
- Relation to us: our synthesizer is a prompt-based fusion (their GenFuser role) but constrained
  to the sources; our agreement matrix is a training-free substitute for their PairRanker role.

### 3. RAG Ensemble — Chen, Dong, Zhu, Dou, arXiv:2508.13828 (2025)
- What they did: first systematic study of ensembling multiple RAG *systems* (pipeline level:
  Branching/Iterative/Loop/Agentic; module level: Generator/Retriever/Reranker), with an
  information-entropy theoretical analysis. Found aggregation generalizable and robust.
- What they did NOT do: the paper does not evaluate this repository's enterprise authorization/audit integration.
  It DOES study different generators over fixed reference documents (Section 4.7, PDF page 8).
- Relation to us: is a direct comparator for shared-evidence generator synthesis. Its published results
  do not establish gains for this workbench; enterprise integration is an implementation distinction,
  not established patent novelty.

### 4. LLM Ensemble survey — Chen et al., IJCAI 2026 (arXiv:2502.18036)
- Taxonomy: ensemble-before / during / after inference. Ours is ensemble-during-inference with an
  after-inference synthesis step. The survey confirms this is an active, recognized field — and
  that most aggregation methods need a judge model or trained fuser. Our deterministic Jaccard
  agreement + source-constrained synthesis avoids both.

### 5. Self-RAG family — Asai et al. 2023; successors (e.g., Reflective RAG, ACL 2026 Findings,
  Wu et al., DOI 10.18653/v1/2026.findings-acl.648)
- What they did: the model itself evaluates retrieved content and its own generation via
  reflection tokens (Self-RAG) or RL-trained critique (Reflective RAG).
- What they did NOT do: single-model introspection; requires training the model.
- Relation to us: we replace self-reflection with CROSS-MODEL consensus — no training, works with
  off-the-shelf local models, and a second opinion from a different model family is a stronger
  error signal than one model grading its own output.

### 6. Self-Consistency — Wang et al. (2022)
- Same model sampled many times at high temperature, majority vote. Diversity from sampling noise
  only; needs canonical answer formats for voting. We use different model families at low
  temperature and generative merging (free-text cited answers don't vote well).

### 7. Iterative Consensus Ensemble (ICE) — 2025, Computers in Biology and Medicine
  (S0010482525010820)
- Models critique each other over multiple rounds until consensus. High latency; critique text can
  drift from the evidence. We do one round with NO model-to-model critique channel: models never
  see each other's answers; only the synthesizer does, re-grounded in the sources.

### 8. Multi-agent RAG (MA-RAG) — Springer, 10.1007/978-3-032-05179-0_22
- Decomposes reasoning into specialized agents (query reformulation, retrieval refinement,
  hallucination detection, answer validation). Different axis: agent specialization, not
  multi-model consensus over shared evidence.

## Question 2: What did the project's own documents say (before this feature)?

From `Research_Paper.pdf` (manuscript draft, 8 Sep 2026) and `SIH_Documentation.pdf` (dossier v1.0):
- The documented system is SINGLE-model: evidence-gated local retrieval (thresholds 0.30/0.45),
  one generation, citations, owner approval for the report tool, append-only audit.
- The paper's own "Discussion" (p.9) flags exactly the gap this feature fills: "Model routing or
  larger models should be added only with measurements showing their benefit for that workload"
  and lists provenance-aware memory and stronger evaluation as priorities.
- The paper's load results (20,000 requests per stage, zero errors, p95 7.5–102 ms across 1–100
  concurrent clients) are for the API layer, not generation; multi-model fan-out multiplies
  generation load and needs its own measurement (noted as future work).
- The paper's references [1] (RAG, Lewis et al. 2020) and [2] (ReAct, Yao et al.) ground the
  single-model design; the multi-model ensemble literature above extends that lineage.

## Question 3: What we are using (our implementation)

Stack: React+TS/Vite UI · Go+Gin control plane (auth, RBAC, audit) · Python+FastAPI AI service ·
PostgreSQL+pgvector · Redis · MinIO · any OpenAI-compatible local endpoint (Ollama/vLLM/LM Studio).

Pipeline (all in-repo, tested):
1. One workspace-scoped pgvector retrieval, focused evidence (mandatory workspace_id predicate).
2. Parallel fan-out to up to 6 local models, same numbered evidence block, grounded prompt.
3. Deterministic pairwise Jaccard agreement matrix (no model judges another).
4. Citation extraction mapping [n] markers to filename+location.
5. Synthesizer merges answers under the source constraint.
6. Existing grounding verifier checks the merged answer (claims → confidence → decision).
7. Append-only audit event + UI panel (combined answer, agreement, per-model details).

Files: `services/ai/app/multi_model.py`, `services/ai/app/internal_api.py`,
`apps/api/internal/ask/multi_model.go`, `apps/web/src/Workbench.tsx`, `apps/web/src/api.ts`,
tests in `services/ai/tests/{unit,integration}/test_multi_model.py`.

## Source list

- MoA paper: https://arxiv.org/abs/2406.04692 · code: https://github.com/togethercomputer/moa
- LLM-Blender: ACL 2023, DOI 10.18653/v1/2023.acl-long.792 · https://github.com/avnlp/llm-blender
- RAG Ensemble: https://arxiv.org/abs/2508.13828
- LLM Ensemble survey: https://arxiv.org/abs/2502.18036 (IJCAI 2026; survey repo
  https://github.com/junchenzhi/Awesome-LLM-Ensemble)
- Ensemble LLMs survey (Mienye & Swart, Information 16(8):688, 2025): DOI 10.3390/info16080688
- Reflective RAG: DOI 10.18653/v1/2026.findings-acl.648
- ICE: https://www.sciencedirect.com/science/article/pii/S0010482525010820
- MA-RAG: https://link.springer.com/chapter/10.1007/978-3-032-05179-0_22
- Self-Consistency: Wang et al., 2022 (arXiv:2203.11171) [standard reference; not re-fetched]
- RAG survey (Zhao et al., Data Science and Engineering 2026): DOI 10.1007/s41019-025-00335-5
- Project documents: Research_Paper.pdf, SIH_Documentation.pdf (8 Sep 2026 drafts, in repo root)
