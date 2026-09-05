# Architectural Decisions

## ADR-001 — PostgreSQL + pgvector before Qdrant

Status: Accepted (2026-09-06)

Reason:
- reduces operational complexity for MVP (one datastore for control plane + vectors)
- sufficient for initial corpus scale
- keeps chunks/metadata and embeddings co-located for workspace-scoped queries

Revisit when:
- vector corpus exceeds benchmark threshold
- retrieval latency becomes unacceptable

## ADR-002 — Go owns authorization; Python owns reasoning

Status: Accepted (2026-09-06)

Reason: single authorization path (Go middleware), AI service receives
already-resolved auth context; prevents two divergent RBAC implementations.

## ADR-003 — Redis for ingestion queue + task events

Status: Accepted (2026-09-06)

Reason: already required for cache/rate-limit; Kafka unjustified at this scale.
Revisit if ingestion throughput requires replayable streams.

## ADR-004 — Forge migration = port engine pieces, build orchestration fresh

Status: Accepted (2026-09-06)

Reason: Forge baseline (docs/forge-baseline.md) shows planner/executor/state/
tools are empty stubs; confidence/graph/context/verifier/model-client are real.

## ADR-005 — Migration tooling: golang-migrate with plain SQL files

Status: Accepted (2026-09-06)

Reason: deterministic, reviewable SQL; no ORM magic for schema changes.
