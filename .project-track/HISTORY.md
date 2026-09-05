# Build History

## Session Start — 2026-09-06

Resumed from:
(nothing — program bootstrap)

Target:
P1-F-000 foundation + Phase A discovery

Expected outcome:
Private repo with discovery docs, Forge baseline, compose/CI/migrations,
runnable service skeletons, first green commit pushed.

## 2026-09-06 — Program bootstrap + Project 1 Phase A

Completed:
- ~/bin tooling installed (repo now PRIVATE-only, ac, feature-done, track-progress)
- Forge reference cloned, baseline run recorded in docs/forge-baseline.md
- sih-build-control master tracker created (private repo, pushed)
- sih-agentic-workbench private repo created (visibility verified)
- Phase A docs: requirements, user-stories, architecture, threat-model, testing
- forge-migration.md + backlog.md

Tests: not yet applicable (docs only)

Notes:
Forge engine components (confidence/graph/context/verifier/model client) are
real and portable; agent planner/executor/state/tools are empty files in Forge
and must be implemented fresh here.

## 2026-09-06 — P1-F-000 Foundation

Completed:
- docker-compose.yml: postgres+pgvector, redis, minio, api, ai, web (healthchecks)
- initial migration 0001_init.sql (16 core tables incl. pgvector schema, audit, approvals, memory)
- Go API: config, db pool, migration runner (unit-tested), health server with
  required/optional dependency checks (unit-tested), main with graceful shutdown
- Python AI service: pydantic settings with sovereign-mode policy validation
  (6 unit tests), FastAPI healthz with honest component reporting (2 integration tests)
- Web: Vite + React + TS + Tailwind v4 + TanStack Query shell, builds clean
- GitHub Actions CI: api / ai / web jobs + integration job with service containers
- Makefile contract: dev/build/lint/test/test-unit/test-integration/seed/clean (venv-aware)
- Live smoke test: full compose up green, migrations applied at API boot,
  integration test passed against live postgres (16 tables + pgvector verified)

Tests:
- go build/vet/test: PASS (httpapi, migrate)
- go integration (live postgres): PASS
- python unit 6/6 PASS, integration 2/2 PASS
- make lint / make test: PASS
- CI: pending first push

Commit: foundation commit (2026-09-06)

Notes:
- Local postgres already occupied 5432; compose host port remapped to 5433 in
  local .env (not committed).
- AI service health honestly reports model_endpoint down — BLOCK-001 confirmed live.

## 2026-09-06 — CI green

- Fixed gofmt check expression in ci.yml and gofmt-formatted 3 Go files
- CI run 33991436900: all 4 jobs PASS (api, ai, web, integration)
- Verified commit: e765ac5

## 2026-09-06 — P1-F-001 Authentication DONE

Completed:
- bcrypt + JWT (HS256, TTL configurable), generic 401 with timing equalization
- login endpoint + auth middleware + /auth/me; bootstrap admin on empty users table
- append-only audit on login success/failure
- 10 auth unit tests; integration TestLoginFlow (6 subtests) vs live postgres
- live verification through running container (token → /auth/me roundtrip)
- Makefile: .env-aware; integration tests isolated to workbench_test DB

Tests:
- unit PASS, integration PASS, CI PASS (prior commit e765ac5)

Commit: P1-F-001 feature-done commit (this push)

Notes:
Bootstrap admin semantics: only when users table empty. Test data pollution of
dev DB caused a false negative — resolved via dedicated workbench_test DB.

## 2026-09-06 — Project 1 PAUSED by user decision

The user ordered the program to move to Project 2 before the P1 release gate.
Gate status: NOT_READY (1 of 19 features done; no waiver of quality — only of sequence).
Resume path: .project-track/handoff.md next_action (P1-F-002/003 orgs+workspaces).
