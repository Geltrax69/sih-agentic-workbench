# Forge Migration Plan

Forge (commit 55b03e3) is the reference implementation; the workbench ports
its engine pieces and generalizes them from "software engineering assistant"
to "enterprise confidential-data workbench". No git history is shared.

## Migration table (updated as work proceeds)

| Forge Area | Current Role | Reuse? | New Workbench Destination | Status | Action |
|---|---|---:|---|---|---|
| `agent/confidence.py` | confidence/refusal gate | Yes | `services/ai/workbench/grounding/confidence.py` | PENDING | port + generalize evidence sources (doc/vector/graph/tool/human) |
| `graph/` | typed knowledge graph | Yes | `services/ai/workbench/knowledge/graph/` | PENDING | adapt; add workspace_id to every node; persist to PostgreSQL |
| `context/builder.py` | grounded context construction | Yes | `services/ai/workbench/grounding/context_builder.py` | PENDING | generalize to context packets w/ token budget + citation map |
| `agent/verifier.py` | Go code verification | Partial | `services/ai/workbench/verification/` | PENDING | convert to generic Verifier interface (Go/Python/JSON/SQL/report/citation) |
| `knowledge/packages.py` | verified knowledge facts | Partial | `services/ai/workbench/knowledge/verified.py` | PENDING | redesign as verified memory items w/ provenance |
| `models/inference.py` | OpenAI-compatible model client | Yes | `services/ai/workbench/models/` | PENDING | generalize to adapter protocol + health + routing + sovereign allowlist |
| `memory/` (design) | external memory artifacts | Yes | `services/ai/workbench/memory/` | PENDING | layered memory (session/workspace/knowledge/experience/decision/audit) |
| `planner/pipeline.py` | deterministic pipeline | Reference | — | N/A | shape reference only |
| `experiments/` | benchmark evidence | Yes | `tests/evaluation/forge_baseline/` | PENDING | preserve benchmark categories as eval suite |
| `agent/planner.py` | (empty in Forge) | No | `services/ai/workbench/orchestration/planner.py` | PENDING | implement: bounded DAG plans |
| `agent/executor.py` | (empty in Forge) | No | `services/ai/workbench/orchestration/executor.py` | PENDING | implement: capability-secured execution |
| `agent/state.py` | (empty in Forge) | No | `services/ai/workbench/orchestration/state.py` | PENDING | implement: persisted task state machine |
| `agent/reflector.py` | (empty in Forge) | No | optional post-MVP evaluator | DEFERRED | |
| `tools/` | (empty in Forge) | No | `services/ai/workbench/tools/` | PENDING | implement: registry + 4 MVP tools |

## Forge principles preserved verbatim

1. The model is never the source of truth — evidence is.
2. Knowledge lives outside model weights (files → DB/graph/vectors here).
3. Confidence gate before tokens are spent.
4. If software can verify it deterministically, don't ask the LLM.
5. Model is interchangeable; no model name in domain logic.
6. Deterministic repair before model repair (goimports lesson).
7. Refuse when there is no evidence.

## Migration order (from plan §92)

Skeleton → model adapter → confidence gate → graph → context builder →
verifier interface → persistence → ingestion/vector → planner → executor →
state → tools → approvals → audit → memory → UI → security/eval → demo.

Each port follows the checklist: identify path → understand deps → remove
project assumptions → add types + workspace context + structured errors +
logs → unit tests → integration test → provenance note in this file →
commit as one increment.
