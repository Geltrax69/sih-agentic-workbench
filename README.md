# Sovereign Agentic AI Workbench (SIH 2026 — Project 1)

An on-premise agentic AI workspace for confidential organizational data.
Models run locally; documents, code, spreadsheets and images stay inside the
organization's infrastructure. Agents reason over ingested knowledge with
citations, use capability-secured tools, require human approval for dangerous
actions, and leave a complete audit trail.

Technical lineage: generalizes the grounding / knowledge-graph /
deterministic-verification architecture of
[Forge](https://github.com/Geltrax69/Forge-A-Self-Evolving-Software-Engineering-System)
into an enterprise workbench. See `docs/forge-migration.md`.

## Stack

- **Web** — React + TypeScript (Vite), Tailwind, TanStack Query, Zod, React Hook Form
- **Control plane API** — Go + Gin (auth, orgs, workspaces, RBAC, tasks, approvals, audit)
- **AI service** — Python + FastAPI (ingestion, embeddings, hybrid retrieval, graph, planning, model adapters)
- **Data** — PostgreSQL (+ pgvector), Redis, MinIO
- **Models** — any OpenAI-compatible local endpoint (Ollama / vLLM / LM Studio); cloud disabled by default
- **Infra** — Docker Compose, GitHub Actions

## Quick start (development)

```bash
cp .env.example .env
make dev        # docker compose up: postgres, redis, minio, api, ai, web
```

Web: http://localhost:3000 — API: http://localhost:8080/healthz

Default dev bootstrap credentials are in `.env.example` (change for anything
beyond local development).

## Repository layout

```text
apps/web/         React front-end
apps/api/         Go control-plane API
services/ai/      Python AI service
migrations/       SQL migrations
scripts/          dev/seed/demo scripts
tests/            integration, e2e, security, evaluation suites
docs/             architecture, requirements, threat model, testing, demo
.project-track/   persistent build tracker (source of truth for progress)
```

## Development commands

```bash
make dev            # start the full stack
make build          # build all components
make lint           # lint everything
make test           # all fast tests
make test-unit      # unit tests
make test-integration  # integration tests (needs docker services)
make test-e2e       # end-to-end scenarios
make seed           # load demo dataset
make clean          # remove build artifacts
```

## Status

Project 1 of 5 in the SIH 2026 sequential build program.
Current state: see `.project-track/CURRENT.md` and `.project-track/handoff.md`.

## License

Proprietary — private repository (SIH 2026 submission project).
