//go:build integration

// Integration tests require a real PostgreSQL. Point DATABASE_URL at a test
// database (docker compose up postgres) and run:
//
//	go test -tags=integration ./...
package integration

import (
	"context"
	"os"
	"testing"

	"github.com/Geltrax69/sih-agentic-workbench/apps/api/internal/db"
	"github.com/Geltrax69/sih-agentic-workbench/apps/api/internal/migrate"
)

func TestMigrationsApplyAgainstRealPostgres(t *testing.T) {
	dsn := os.Getenv("DATABASE_URL")
	if dsn == "" {
		t.Skip("DATABASE_URL not set — skipping integration test")
	}

	ctx := context.Background()
	pool, err := db.Connect(ctx, dsn)
	if err != nil {
		t.Fatalf("connect: %v", err)
	}
	defer pool.Close()

	migrationDir := os.Getenv("MIGRATIONS_DIR")
	if migrationDir == "" {
		migrationDir = "../../../../migrations" // package dir → repo root
	}

	applied, err := migrate.Apply(ctx, db.Pool{Pool: pool}, migrationDir)
	if err != nil {
		t.Fatalf("apply migrations: %v", err)
	}
	if len(applied) == 0 {
		t.Log("no new migrations applied (already migrated) — acceptable")
	}

	// Re-running must be idempotent.
	again, err := migrate.Apply(ctx, db.Pool{Pool: pool}, migrationDir)
	if err != nil {
		t.Fatalf("re-apply migrations: %v", err)
	}
	if len(again) != 0 {
		t.Fatalf("second apply ran %v — migrations must be idempotent", again)
	}

	// Core tables from 0001_init must exist.
	for _, table := range []string{
		"users", "organizations", "workspaces", "workspace_members",
		"documents", "document_chunks", "ingestion_jobs", "tasks",
		"task_steps", "tool_executions", "approvals", "audit_events",
		"memory_items", "model_configs", "knowledge_nodes", "knowledge_edges",
	} {
		var exists bool
		err := pool.QueryRow(ctx,
			"SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = $1)",
			table).Scan(&exists)
		if err != nil {
			t.Fatalf("check table %s: %v", table, err)
		}
		if !exists {
			t.Errorf("expected table %s to exist after migrations", table)
		}
	}

	// pgvector extension must be usable.
	var ext string
	if err := pool.QueryRow(ctx,
		"SELECT extname FROM pg_extension WHERE extname = 'vector'").Scan(&ext); err != nil {
		t.Errorf("vector extension missing: %v", err)
	}
}
