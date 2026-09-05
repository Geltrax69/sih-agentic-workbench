# Session Handoff

Read this file before changing code.

## Project

sih-agentic-workbench
Project 1 of 5 (program tracker: ~/PROJECTS/sih-build-control)

## Current State

Foundation (P1-F-000) is complete and was verified green before commit:
full docker compose stack boots, migrations apply at API boot, all unit and
integration tests pass, `make lint` and `make test` are green from repo root.

Next feature: P1-F-001 Authentication.

## Work Completed This Session

- Phase A discovery docs (requirements, user-stories, architecture, threat-model, testing)
- Forge baseline (docs/forge-baseline.md) + migration plan (docs/forge-migration.md)
- docker-compose.yml (postgres+pgvector, redis, minio, api, ai, web)
- migrations/0001_init.sql — 16 core tables
- Go API skeleton: config, db, migrate runner, health server, main (build/vet/test green)
- Python AI service skeleton: sovereign-mode config policy + FastAPI healthz (8 tests green)
- Web shell: Vite+React+TS+Tailwind+TanStack Query (build green)
- GitHub Actions CI workflow (4 jobs)
- Makefile contract (dev/build/lint/test/test-integration/seed/clean), venv-aware

## Work Not Yet Completed

- P1-F-001 Authentication (next)
- P1-F-002..019 per features.json
- CI not yet observed on GitHub (runs on first push)

## Files Most Relevant Next

- apps/api/internal/httpapi/server.go (add /api/v1/auth/login + protected routes)
- apps/api/internal/config/config.go (bootstrap admin envs already present)
- migrations/ (users table exists in 0001)
- docs/architecture.md (responsibility split)

## Do Not Change

- Go owns authorization / Python owns reasoning boundary (ADR-002)
- pgvector before Qdrant (ADR-001)
- health semantics: ai_service/model endpoint are OPTIONAL dependencies (must stay honest, not fatal)
- task state names and audit append-only design (migration 0001)

## Next Exact Task

Implement P1-F-001 Authentication:
1. apps/api/internal/auth: bcrypt hashing, JWT issue/verify with unit tests
2. POST /api/v1/auth/login (rate-limit later), bootstrap admin on startup
3. Auth middleware protecting /api/v1/*
4. Integration test: login ok → 200 + token; wrong password → 401; no token on protected route → 401

Then run:
make lint
make test

If green: update tracker, feature-done "feat: add authentication with jwt and bootstrap admin"

## Release Gate

NOT READY

Do not begin Project 2.
