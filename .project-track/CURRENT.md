# Current Build State

Project: sih-agentic-workbench
Project number: 1 of 5
Phase: Core Domain (Phase C)
Overall status: In Progress
Estimated completion: 6% (derived from features.json weights: P1-F-001 done, weight 5 of 81)

## Current Feature

Next: P1-F-002 — Organizations (then P1-F-003 Workspaces, P1-F-004 RBAC)

Status:
NOT_STARTED

## What Already Works

- P1-F-000 foundation: compose stack (6 services), migrations, health endpoints, CI
- P1-F-001 Authentication:
  - POST /api/v1/auth/login — bcrypt verify, generic 401 (unknown email vs bad password indistinguishable, timing-equalized)
  - JWT sessions (HS256, 24h TTL configurable via JWT_TTL_HOURS)
  - auth middleware protecting /api/v1/* group; GET /api/v1/auth/me returns claims
  - bootstrap admin created on startup when users table is empty (verified live)
  - login success/failure written to append-only audit_events (verified in DB)
- Go unit tests green; auth integration suite green against live postgres (workbench_test DB)
- Live end-to-end verified: login via running container → token → /auth/me roundtrip

## Tests

- unit: PASS
- integration: PASS (migrations + full login flow incl. audit rows)
- E2E: NOT_RUN
- security: PARTIAL (timing-equalized login, generic errors; isolation tests come with P1-F-002..004)
- CI: PASS (will re-run on this push)

## Known Issues

- BLOCK-001: no local model endpoint running — does not block orgs/workspaces/RBAC

## Last Verified Commit

see .project-track/status.json last_verified_commit (feature-done commit for P1-F-001)

## Next Exact Action

Implement P1-F-002/003 Organizations + Workspaces:
1. internal/orgs: org + workspace stores (SQL), handlers: POST/GET /api/v1/workspaces
2. Membership checks middleware (workspace_id scoped), cross-workspace denial → 403 + audit
3. Unit tests for membership logic; integration tests: create org/workspace, list only mine, foreign workspace access denied
Then make lint && make test && make test-integration, update tracker, feature-done.
