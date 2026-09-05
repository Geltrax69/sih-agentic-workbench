# Session Handoff

Read this file before changing code.

## Project

sih-agentic-workbench
Project 1 of 5 (program tracker: ~/PROJECTS/sih-build-control)

## Current State

P1-F-001 Authentication is DONE and verified: unit + integration green,
live end-to-end login verified against the running compose stack
(bootstrap admin → token → /auth/me), audit rows confirmed.

Next feature: P1-F-002 Organizations (+ P1-F-003 Workspaces, P1-F-004 RBAC).

## Work Completed This Session

- internal/auth: password.go (bcrypt + timing equalizer), jwt.go (HS256 issue/parse),
  service.go (Login, BootstrapAdmin), middleware.go (Bearer middleware + context keys),
  handler.go (login + /auth/me routes)
- internal/users store, internal/audit append-only recorder
- main.go: bootstrap admin on startup, public /api/v1/auth/login, protected /api/v1 group
- config: JWT_TTL_HOURS
- tests: 10 auth unit tests; integration TestLoginFlow (6 subtests incl. audit verification)
- Makefile: reads .env; test-integration uses dedicated workbench_test DB
  (dev DB stays clean; CI parity)

## Gotchas Discovered

- Bootstrap admin only created when users table is EMPTY. Integration tests
  seeding users into the dev DB previously blocked it — tests now run against
  workbench_test via `make test-integration`.
- Host port for postgres is 5433 locally (5432 occupied) — recorded in .env,
  Makefile includes it.

## Files Most Relevant Next

- apps/api/cmd/api/main.go (route wiring pattern: public group + protected group)
- apps/api/internal/auth/middleware.go (context keys to reuse for RBAC)
- migrations/0001_init.sql (organizations, organization_members, workspaces, workspace_members exist)
- docs/architecture.md (Go owns authorization)

## Do Not Change

- Go owns authorization / Python owns reasoning (ADR-002)
- audit is append-only (no update/delete paths)
- login errors are generic (no user enumeration)
- health semantics: model endpoint optional, postgres/redis required

## Next Exact Task

P1-F-002/003: organizations + workspaces CRUD with membership middleware.
Integration test must include cross-workspace denial (403) + audit event.

Then run:
make lint
make test
make test-integration

If green: update tracker, feature-done "feat: add organizations and workspaces with membership checks"

## Release Gate

NOT READY

Do not begin Project 2.
