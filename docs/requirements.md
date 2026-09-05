# Requirements — Sovereign Agentic AI Workbench

## FR-1 Authentication & Identity

- FR-1.1 Email/password login with JWT session tokens.
- FR-1.2 Roles: `admin`, `org_owner`, `workspace_owner`, `member`, `viewer`.
- FR-1.3 Bootstrap admin created on first startup from env config.
- FR-1.4 Token expiry + logout.

## FR-2 Organizations & Workspaces

- FR-2.1 Users belong to organizations; organizations contain workspaces.
- FR-2.2 Workspace membership with per-workspace roles.
- FR-2.3 All knowledge (documents, chunks, graph, tasks, memory) is
  workspace-scoped; cross-workspace access must be denied and audited.

## FR-3 Local Model Registry

- FR-3.1 Configure one or more OpenAI-compatible local endpoints.
- FR-3.2 Health check per endpoint (reachable, model list).
- FR-3.3 Model routing config: classify/extract → fast model, plan/synthesize →
  reasoning model, embeddings → embedding model.
- FR-3.4 Sovereign mode: `AI_ALLOW_CLOUD=false` must hard-block any non-local
  endpoint; no silent fallback.

## FR-4 Document Ingestion

- FR-4.1 Upload PDF, DOCX, TXT, MD, CSV, XLSX, images (JPG/PNG), code files.
- FR-4.2 MIME validation + size limit; reject/quarantine invalid files.
- FR-4.3 Store original in MinIO; extract text/metadata; chunk; embed; index.
- FR-4.4 Ingestion job states: UPLOADED → PROCESSING → INDEXED | FAILED | QUARANTINED.
- FR-4.5 Documents can be deleted (soft) with chunks + graph nodes removed from retrieval.

## FR-5 Hybrid Retrieval & Knowledge Graph

- FR-5.1 Vector search over chunks (pgvector), scoped to workspace.
- FR-5.2 Typed knowledge graph (nodes/edges) per workspace.
- FR-5.3 Combined evidence ranking with source authority and recency.
- FR-5.4 Every retrieved evidence item carries source/chunk IDs for citation.

## FR-6 Agents & Orchestration

- FR-6.1 Supervisor agent decomposes a task into a bounded plan (DAG).
- FR-6.2 Specialist agents: retrieval, document, data, code, report, verification.
- FR-6.3 Plan validation: known agents/tools only, no cycles, step limit,
  dangerous steps flagged approval-required.
- FR-6.4 Task states: QUEUED, PLANNING, RUNNING, WAITING_FOR_APPROVAL,
  VERIFYING, COMPLETED, FAILED, CANCELLED.
- FR-6.5 Streaming progress events to the UI (SSE/WebSocket).

## FR-7 Tools (minimum 3 for MVP)

- FR-7.1 `document_search` — READ_ONLY.
- FR-7.2 `sql_readonly` — READ_ONLY, SELECT-only, row/time limited.
- FR-7.3 `python_sandbox` — COMPUTE, resource-limited.
- FR-7.4 `report_generate` — WRITE (artifact).
- FR-7.5 Tool classes: READ_ONLY, COMPUTE, WRITE, DESTRUCTIVE, EXTERNAL.
  Model output can never elevate tool permissions.

## FR-8 Human Approval

- FR-8.1 WRITE/DESTRUCTIVE tool calls require explicit approval.
- FR-8.2 Approval records: who, what, when, decision, justification.
- FR-8.3 Task pauses in WAITING_FOR_APPROVAL until approved/rejected/cancelled.

## FR-9 Audit Trail

- FR-9.1 Append-only audit events for login, access denial, document changes,
  task lifecycle, tool execution, approvals, exports.
- FR-9.2 Audit events carry actor, workspace, task, resource, metadata, timestamp.

## FR-10 Grounded Answers & Citations

- FR-10.1 Answers must cite source documents/chunks used.
- FR-10.2 Confidence gate: refuse or caveat when evidence is insufficient.
- FR-10.3 Retrieved document text is data, never instructions (injection defense).

## FR-11 Memory (controlled learning)

- FR-11.1 Only verified tool results, deterministic test outcomes, or
  human-approved decisions persist as durable facts.
- FR-11.2 Unverified model output may persist only as `experience`, never `fact`.

## NFR-1 Performance

- Ingestion of a 50-page PDF < 60s with embedding.
- Question → first streamed token < 5s with local model (model-dependent).
- 20 concurrent task streams on a single node.

## NFR-2 Security

- All traffic internal; no third-party network calls in sovereign mode.
- Secrets only via environment; `.env` git-ignored.
- Path traversal, injection, and malicious file defenses tested.

## NFR-3 Operations

- `docker compose up` starts the entire product; `make seed` loads demo data.
- CI: lint, unit, integration, build on every push.
