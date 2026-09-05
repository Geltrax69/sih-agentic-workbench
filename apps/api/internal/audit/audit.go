// Package audit appends immutable audit events. There is deliberately no
// update or delete path: audit data is write-only.
package audit

import (
	"context"
	"encoding/json"
	"log/slog"

	"github.com/jackc/pgx/v5/pgxpool"
)

// Recorder writes audit events to PostgreSQL.
type Recorder struct {
	pool *pgxpool.Pool
}

func NewRecorder(pool *pgxpool.Pool) *Recorder { return &Recorder{pool: pool} }

// Event inserts one audit event. Metadata may be nil. Failures are logged,
// never panic the caller: losing an audit write must not take down a request,
// but it must be visible in logs.
func (r *Recorder) Event(ctx context.Context, userID, taskID, workspaceID, eventType, resourceType, resourceID string, metadata map[string]any) {
	meta := []byte("{}")
	if metadata != nil {
		b, err := json.Marshal(metadata)
		if err != nil {
			b = []byte(`{"metadata_error": true}`)
		}
		meta = b
	}
	_, err := r.pool.Exec(ctx, `
		INSERT INTO audit_events (user_id, task_id, workspace_id, event_type, resource_type, resource_id, metadata)
		VALUES (NULLIF($1,'')::uuid, NULLIF($2,'')::uuid, NULLIF($3,'')::uuid, $4, $5, $6, $7::jsonb)`,
		userID, taskID, workspaceID, eventType, resourceType, resourceID, string(meta))
	if err != nil {
		slog.Error("audit write failed", "event_type", eventType, "err", err)
	}
}
