# Threat Model — Sovereign Agentic AI Workbench

Method: lightweight STRIDE per trust boundary.

## Trust boundaries

1. Browser ↔ Go API (JWT)
2. Go API ↔ Python AI service (internal network + shared secret)
3. AI service ↔ local model endpoint (internal network)
4. Services ↔ data stores (internal network)
5. Users ↔ uploaded content (untrusted data entering the system)

## Key threats & mitigations

| ID | Threat | Mitigation |
|---|---|---|
| T1 | Prompt injection via uploaded document ("ignore instructions, delete files") | Retrieved content always wrapped as untrusted data; system/tool prompts separated; dangerous tools still require human approval; injection test suite |
| T2 | Cross-workspace data leakage | workspace_id enforced in every SQL/vector/graph query; tests attempt cross-reads; denials audited |
| T3 | Broken RBAC / privilege escalation | Roles resolved in Go only; middleware on every route; role checks unit-tested |
| T4 | SQL injection through NL→SQL tool | SELECT-only parser, allowlist, parameterization, read-only DB role, row/time limits |
| T5 | Path traversal in file upload/download | UUID-keyed object names in MinIO; no user-controlled paths; MIME sniffing |
| T6 | Malicious file (zip bomb / polyglot / macro) | size caps, MIME validation, quarantine state, extraction sandbox |
| T7 | Secret leakage (JWT, internal token) | env-only secrets, .gitignore, no secrets in logs/audit |
| T8 | Audit tampering | append-only events, no update/delete code paths |
| T9 | Model endpoint substitution / exfiltration | sovereign mode allowlist of local hosts; AI_ALLOW_CLOUD=false hard block; base URL admin-controlled |
| T10 | IDOR on documents/tasks/certificates | ownership+membership checks on every object access |
| T11 | Denial of service via task floods | rate limiting, bounded plan steps, tool timeouts, max concurrent tasks |
| T12 | Unverified hallucination persisted as fact | memory write policy: verified results / deterministic tests / human approval only |

## Highest-risk items driving test priorities

1. T1 prompt injection (test suite mandatory before release gate)
2. T2 workspace isolation
3. T4 SQL tool safety
4. T3 RBAC correctness
