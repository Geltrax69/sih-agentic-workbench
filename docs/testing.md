# Testing Strategy — Sovereign Agentic AI Workbench

Pyramid: many unit tests, focused integration tests, few E2E journeys,
plus security and evaluation suites.

## Layers

| Layer | Scope | Location | Speed |
|---|---|---|---|
| Unit | chunking, permissions, confidence, plan validation, tool schemas, tolerance of prompts, citation mapping | Go `*_test.go`, Python `tests/unit` | seconds |
| Integration | upload→extract→embed→retrieve; auth→task→tool→result; RBAC across workspaces; model adapter against stub endpoint | `tests/integration` (docker services) | minutes |
| E2E | login → workspace → upload → grounded Q → cited answer → report → approval → audit | `tests/e2e` | minutes |
| Security | injection, cross-workspace, SQL write attempts, path traversal, malicious files | `tests/security` | minutes |
| Evaluation | retrieval relevance, citation correctness, injection resistance, routing | `tests/evaluation` | on demand |

## Command interface

```bash
make test-unit
make test-integration
make test-e2e
make test-security
```

## Mandatory test cases (from plan §19/§91)

- Confidence gate: verified evidence → answer; partial → warn; none → refuse;
  wrong-workspace evidence never counts; stale/revoked down-weighted.
- Planner: valid DAG, cycle rejection, unknown tool, unauthorized tool,
  step limit, dangerous step must require approval.
- Executor: invalid args, permission denial, approval required, timeout,
  crash, verification failure.
- Ingestion: each file type, corrupt file, oversize, wrong MIME.
- Isolation: user A cannot list/read/search workspace B by any API.
- SQL tool: SELECT passes; UPDATE/DELETE/DROP rejected pre-execution.
- Injection: hidden instruction in document, fake SYSTEM text, tool command
  in source, exfiltration request, encoded payload.
- Memory: unverified speculation rejected; verified lesson persists.

## CI

GitHub Actions on push/PR: fmt/lint → unit → integration (service containers)
→ build (Go, web, AI image). E2E on main + manual dispatch.

## Rules

- Never mark a test passed without running it.
- Every fixed bug gets a regression test where feasible.
- Evaluation results stored as data under `tests/evaluation/results/`.
