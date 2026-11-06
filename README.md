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

## Run the application

### Full application (recommended)

You need Docker Desktop, LM Studio with its `lms` command-line tool enabled, and
the three local models used by the default configuration:

- `minicpm5-1b`
- `gemma-4-e4b-it-obliterated`
- `text-embedding-nomic-embed-text-v1.5`

Create your local configuration once, then start the full stack:

```bash
cp .env.example .env
./run.sh
```

The script starts Docker Desktop when needed, loads the local models, starts LM
Studio on port 1234, builds the services, and opens the app. Visit
http://localhost:3000 and sign in with `BOOTSTRAP_ADMIN_EMAIL` and
`BOOTSTRAP_ADMIN_PASSWORD` from `.env`.

To start without opening a browser:

```bash
NO_BROWSER=1 ./run.sh
```

To stop the application while preserving its database and uploaded documents:

```bash
docker compose down
```

To also remove local Docker data, run `docker compose down -v`.

### UI preview only

Use this when you only want to view the interface with sample data; it does not
start Docker, call the API, or require local AI models.

```bash
cd apps/web
npm install
npm run dev -- --host 127.0.0.1
```

Open http://127.0.0.1:3000/?preview=1. Stop the preview with `Ctrl+C`.

### Manual full-stack startup

If LM Studio is already running and configured in `.env`, start the services with:

```bash
docker compose up --build
```

Web: http://localhost:3000 — API health check: http://localhost:8080/healthz

The default development credentials are listed in `.env.example`; change them
before using any non-local environment.

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
