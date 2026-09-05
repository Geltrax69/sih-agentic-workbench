-- 0001_init.sql — core schema for the Sovereign Agentic AI Workbench
-- Applied by the API's migration runner (tracked in schema_migrations).

CREATE EXTENSION IF NOT EXISTS vector;

-- ---------- identity & tenancy ----------

CREATE TABLE IF NOT EXISTS users (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email         TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    display_name  TEXT NOT NULL,
    role          TEXT NOT NULL DEFAULT 'member',  -- global: admin | member
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS organizations (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name       TEXT NOT NULL,
    created_by UUID NOT NULL REFERENCES users(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS organization_members (
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role            TEXT NOT NULL DEFAULT 'member',  -- org_owner | member
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (organization_id, user_id)
);

CREATE TABLE IF NOT EXISTS workspaces (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    name            TEXT NOT NULL,
    description     TEXT NOT NULL DEFAULT '',
    created_by      UUID NOT NULL REFERENCES users(id),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS workspace_members (
    workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    user_id      UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role         TEXT NOT NULL DEFAULT 'member',  -- workspace_owner | member | viewer
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (workspace_id, user_id)
);

-- ---------- documents & ingestion ----------

CREATE TABLE IF NOT EXISTS documents (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    uploaded_by  UUID NOT NULL REFERENCES users(id),
    filename     TEXT NOT NULL,
    mime_type    TEXT NOT NULL,
    size_bytes   BIGINT NOT NULL,
    storage_key  TEXT NOT NULL,              -- MinIO object key (UUID-based)
    status       TEXT NOT NULL DEFAULT 'UPLOADED',  -- UPLOADED|PROCESSING|INDEXED|FAILED|QUARANTINED
    deleted_at   TIMESTAMPTZ,                -- soft delete
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_documents_workspace ON documents(workspace_id) WHERE deleted_at IS NULL;

CREATE TABLE IF NOT EXISTS document_versions (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    version     INT  NOT NULL,
    storage_key TEXT NOT NULL,
    checksum    TEXT NOT NULL DEFAULT '',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (document_id, version)
);

CREATE TABLE IF NOT EXISTS document_chunks (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    chunk_index INT  NOT NULL,
    content     TEXT NOT NULL,
    token_count INT  NOT NULL DEFAULT 0,
    embedding   vector(768),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (document_id, chunk_index)
);
CREATE INDEX IF NOT EXISTS idx_chunks_workspace ON document_chunks(workspace_id);
CREATE INDEX IF NOT EXISTS idx_chunks_embedding ON document_chunks
    USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

CREATE TABLE IF NOT EXISTS ingestion_jobs (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    workspace_id UUID NOT NULL,
    status      TEXT NOT NULL DEFAULT 'PENDING',  -- PENDING|RUNNING|DONE|FAILED
    error       TEXT NOT NULL DEFAULT '',
    started_at  TIMESTAMPTZ,
    finished_at TIMESTAMPTZ,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ---------- knowledge graph ----------

CREATE TABLE IF NOT EXISTS knowledge_nodes (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    type         TEXT NOT NULL,   -- DOCUMENT|DOCUMENT_CHUNK|CODE_FILE|DATASET|POLICY|PROCEDURE|TASK|DECISION|INCIDENT|REPORT|SOURCE...
    title        TEXT NOT NULL,
    metadata     JSONB NOT NULL DEFAULT '{}',
    source_id    UUID,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_nodes_workspace ON knowledge_nodes(workspace_id);

CREATE TABLE IF NOT EXISTS knowledge_edges (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    from_node    UUID NOT NULL REFERENCES knowledge_nodes(id) ON DELETE CASCADE,
    to_node      UUID NOT NULL REFERENCES knowledge_nodes(id) ON DELETE CASCADE,
    type         TEXT NOT NULL,   -- DOCUMENTED_BY|REQUIRES|DEPENDS_ON|REFERENCES|VERIFIED_BY|CAUSED_BY|FIXED_BY|GENERATED_FROM|SUPERSEDES|DERIVED_FROM...
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_edges_workspace ON knowledge_edges(workspace_id);

-- ---------- tasks, tools, approvals ----------

CREATE TABLE IF NOT EXISTS tasks (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    created_by   UUID NOT NULL REFERENCES users(id),
    status       TEXT NOT NULL DEFAULT 'QUEUED',  -- QUEUED|PLANNING|RUNNING|WAITING_FOR_APPROVAL|VERIFYING|COMPLETED|FAILED|CANCELLED
    input        TEXT NOT NULL,
    model_route  TEXT NOT NULL DEFAULT '',
    result       JSONB,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_tasks_workspace ON tasks(workspace_id);

CREATE TABLE IF NOT EXISTS task_steps (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id     UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    step_key    TEXT NOT NULL,
    agent       TEXT NOT NULL,
    action      TEXT NOT NULL,
    depends_on  TEXT[] NOT NULL DEFAULT '{}',
    status      TEXT NOT NULL DEFAULT 'PENDING',
    approval_required BOOLEAN NOT NULL DEFAULT false,
    output      JSONB,
    error       TEXT NOT NULL DEFAULT '',
    started_at  TIMESTAMPTZ,
    finished_at TIMESTAMPTZ,
    UNIQUE (task_id, step_key)
);

CREATE TABLE IF NOT EXISTS tool_executions (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id     UUID REFERENCES tasks(id) ON DELETE CASCADE,
    step_key    TEXT NOT NULL DEFAULT '',
    tool_name   TEXT NOT NULL,
    risk_class  TEXT NOT NULL,   -- READ_ONLY|COMPUTE|WRITE|DESTRUCTIVE|EXTERNAL
    args        JSONB NOT NULL DEFAULT '{}',
    result      JSONB,
    status      TEXT NOT NULL DEFAULT 'PENDING',
    error       TEXT NOT NULL DEFAULT '',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    finished_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS approvals (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    task_id     UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    step_key    TEXT NOT NULL DEFAULT '',
    tool_name   TEXT NOT NULL,
    reason      TEXT NOT NULL DEFAULT '',
    status      TEXT NOT NULL DEFAULT 'PENDING',  -- PENDING|APPROVED|REJECTED
    decided_by  UUID REFERENCES users(id),
    decision_note TEXT NOT NULL DEFAULT '',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    decided_at  TIMESTAMPTZ
);

-- ---------- audit & memory ----------

CREATE TABLE IF NOT EXISTS audit_events (
    id             BIGSERIAL PRIMARY KEY,   -- append-only, ordered
    organization_id UUID,
    workspace_id   UUID,
    user_id        UUID,
    task_id        UUID,
    event_type     TEXT NOT NULL,
    resource_type  TEXT NOT NULL DEFAULT '',
    resource_id    TEXT NOT NULL DEFAULT '',
    metadata       JSONB NOT NULL DEFAULT '{}',
    created_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_audit_workspace_time ON audit_events(workspace_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_task ON audit_events(task_id);

CREATE TABLE IF NOT EXISTS memory_items (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    layer        TEXT NOT NULL,   -- workspace|knowledge|experience|decision
    kind         TEXT NOT NULL,   -- fact|experience|decision
    content      TEXT NOT NULL,
    provenance   JSONB NOT NULL DEFAULT '{}',  -- task/tool/verification refs
    verified     BOOLEAN NOT NULL DEFAULT false,
    revoked_at   TIMESTAMPTZ,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_memory_workspace ON memory_items(workspace_id) WHERE revoked_at IS NULL;

-- ---------- model registry ----------

CREATE TABLE IF NOT EXISTS model_configs (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name        TEXT NOT NULL UNIQUE,     -- fast | reasoning | embedding | vision
    provider    TEXT NOT NULL DEFAULT 'openai_compatible',
    base_url    TEXT NOT NULL,
    model       TEXT NOT NULL,
    is_local    BOOLEAN NOT NULL DEFAULT true,
    enabled     BOOLEAN NOT NULL DEFAULT true,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
