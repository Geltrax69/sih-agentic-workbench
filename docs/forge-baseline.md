# Forge Baseline — recorded before any migration

- **Date:** 2026-09-06
- **Forge commit:** 55b03e3 ("README: explain how Forge works, what's measured, and what's broken")
- **Clone:** ~/PROJECTS/Forge-A-Self-Evolving-Software-Engineering-System
- **Python:** 3.14.7 (system) — Forge is stdlib-only for its core modules
- **Model endpoint at baseline time:** none running (LM Studio default
  127.0.0.1:1234 refused connection)

## What actually runs (verified 2026-09-06)

| Module | Result |
|---|---|
| `python3 -m graph.seed` | ✓ PASS — 5 typed-graph traversal queries answered (docs/files/blast-radius/similar-bugs/tests) |
| `python3 -m context.builder` | ✓ PASS — builds context prompt from docs |
| `python3 -m agent.confidence` | ✓ PASS — scores questions with sources; generic-word stripping works (JWT 1.0 answerable, Redis-Streams 0.5, Chi 1.0) |
| `python3 -m agent.verifier` | ✓ PASS — goimports rescues missing import; go build path OK |
| `python3 -m planner.pipeline` | ✗ FAILS at model call only — deterministic prefix OK; `RuntimeError: LLM unreachable at http://127.0.0.1:1234/v1` (no local endpoint running at baseline time) |

## Component inventory (line counts verified)

| Path | Lines | State |
|---|---:|---|
| `agent/confidence.py` | 71 | WORKING — port+generalize |
| `agent/verifier.py` | 89 | WORKING — convert to verifier interface |
| `agent/planner.py` | 0 | EMPTY — implement fresh |
| `agent/executor.py` | 0 | EMPTY — implement fresh |
| `agent/reflector.py` | 0 | EMPTY — optional, post-MVP |
| `agent/reviewer.py` | 0 | EMPTY |
| `agent/state.py` | 0 | EMPTY — implement fresh |
| `context/builder.py` | 57 | WORKING — generalize |
| `graph/graph.py` | 90 | WORKING — adapt to workspace-scoped graph |
| `graph/schema.py` | 55 | WORKING — extend node/edge types |
| `graph/seed.py` | 57 | WORKING — demo seed reference |
| `models/inference.py` | 45 | WORKING — stdlib OpenAI-compatible client w/ reasoning-model handling; generalize to adapter |
| `planner/pipeline.py` | 102 | WORKING (deterministic stages) — reference for pipeline shape |
| `tools/*` (8 files) | 0 | ALL EMPTY — implement capability-secured tools fresh |
| `experiments/*` | ~6 files | WORKING — preserve as evaluation baselines |
| `requirements.txt` | 0 | EMPTY (stdlib-only core) |

## Known limitations (from Forge's own README + baseline run)

- Learning loop / graph update is "planned", not implemented.
- 1B model envelope: ~1 function / ~30 lines / ~250 output tokens; needs
  evidence in context; temperature 0 loops worse than 0.4.
- The patch loop (not generation) was the historical bottleneck; deterministic
  repair (goimports-first) fixed it — keep this principle.
- No auth, no workspaces, no persistence — everything is in-memory/file-based.

## Conclusion

Forge's five engine components (confidence, graph, context builder, model
client, verifier) are genuine and worth porting. Everything orchestration-
shaped (planner, executor, state, tools) must be built new in the workbench.
The baseline above was produced without modifying Forge.
