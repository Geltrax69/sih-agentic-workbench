# Architecture — Sovereign Agentic AI Workbench

## System overview

```text
Browser (React SPA)
   │  HTTP/SSE
   ▼
Go control plane (Gin)  ──internal API──►  Python AI service (FastAPI)
   │  auth, orgs, workspaces, RBAC           │  ingestion, embeddings,
   │  documents (metadata), tasks,           │  hybrid retrieval, graph,
   │  approvals, audit, events gateway       │  planner, executor, tools,
   │                                         │  model adapters, verifiers
   ▼                                         ▼
PostgreSQL (+pgvector)   Redis          MinIO           Local LLM endpoint
 control-plane data      queues/cache   raw documents   (Ollama/vLLM/LM Studio)
```

## Responsibility split (hard boundary)

- **Go owns authorization.** Every task handed to the AI service carries an
  already-resolved authorization context (user, org, workspace, permissions).
  The AI service never re-derives and never bypasses it.
- **Python owns reasoning.** Extraction, embeddings, retrieval, graph,
  planning, tool execution against model endpoints, verification adapters.
  No enterprise control-plane tables are mutated directly by Python except
  its own AI-side tables (chunks, embeddings, graph, memory).

## Data stores

| Store | Contents |
|---|---|
| PostgreSQL | users, organizations, workspaces, memberships, documents, ingestion_jobs, tasks, task_steps, tool_executions, approvals, audit_events, model_configs, memory_items, knowledge_nodes, knowledge_edges |
| pgvector | document_chunks.embedding (1536-dim default, configurable) |
| Redis | ingestion queue, task event pub/sub, rate limiting |
| MinIO | original uploaded files (bucket per environment) |

## Core pipelines

### Ingestion
upload → MIME/size validation → MinIO → extraction (pdf/docx/csv/xlsx/md/txt/img-metadata)
→ chunking → embedding → pgvector index → optional graph extraction → status.

### Task execution
```text
task created (Go) → internal dispatch (auth context attached)
  → supervisor plans (bounded DAG, validated)
  → executor runs steps:
       permission check → tool lookup → arg validation
       → approval gate (if WRITE/DESTRUCTIVE) → sandboxed run
       → verifier → audit
  → events streamed (SSE) → final artifact → confidence/citation checks
```

## Security invariants

1. Every retrieval query filters by workspace_id. No exception.
2. Retrieved document text is quoted into prompts as untrusted data.
3. Tool permission classes are server-side; model output cannot elevate.
4. SQL tool: parse → SELECT-only → row/time limits → read-only creds.
5. Sovereign mode: base-URL allowlist = local hosts only, enforced at adapter.
6. Audit is append-only; no UPDATE/DELETE paths in code.

## Model routing (from Forge, generalized)

```yaml
routes:
  classify: fast        # small model
  extract: fast
  plan: reasoning       # stronger local model
  synthesize: reasoning
  embed: embedding
```

All model names/endpoints configurable; no model name in domain logic.

## Internal API (Go ↔ Python)

```text
POST /internal/ai/tasks          {task, auth_context}
GET  /internal/ai/tasks/{id}     status/steps/artifacts
POST /internal/ai/health         model endpoints health
```
Protected by `INTERNAL_API_SECRET` (network-restricted + bearer).

## Forge migration summary

See `docs/forge-migration.md` for the component-by-component plan
(confidence gate, graph, context builder, model adapter, verifier are ported
and generalized; planner/executor/state/tools are implemented fresh — they
are empty stubs in Forge).
