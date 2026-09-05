# Test Status

Last updated: 2026-09-06 (foundation session)

## Unit

PASS

Commands:
make test-unit  (go test ./..., pytest tests/unit, npm run build)

Last verified: e765ac5 (2026-09-06)

## Integration

PASS

Commands:
- go:  DATABASE_URL=... go test -tags=integration ./tests/integration/... -count=1
  (verified against live compose postgres: migrations idempotent, 16 tables + pgvector present)
- python: pytest tests/integration (healthz/ping via TestClient)

## E2E

NOT RUN

Reason: no user flows yet — starts after P1-F-001..004 (auth/orgs/workspaces/RBAC).

## Security

NOT RUN

Planned earliest coverage: sovereign-mode endpoint policy (unit tests exist for
config validation), then RBAC + workspace isolation with P1-F-002..004.

## Performance

NOT RUN
