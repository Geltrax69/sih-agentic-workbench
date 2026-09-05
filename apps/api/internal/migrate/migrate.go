// Package migrate applies plain SQL migration files in filename order.
package migrate

import (
	"context"
	"fmt"
	"os"
	"path/filepath"
	"sort"
	"strings"
)

// Executor is the minimal database surface the runner needs.
// db.Pool adapts *pgxpool.Pool to this interface; tests use a fake.
type Executor interface {
	Exec(ctx context.Context, sql string) error
	// QueryString runs a query expected to yield at most one scalar string.
	QueryString(ctx context.Context, sql string) (value string, found bool, err error)
}

// Discover lists migration files (*.sql) under dir sorted by name.
func Discover(dir string) ([]string, error) {
	entries, err := os.ReadDir(dir)
	if err != nil {
		return nil, fmt.Errorf("read migrations dir: %w", err)
	}
	var files []string
	for _, e := range entries {
		if e.IsDir() || !strings.HasSuffix(e.Name(), ".sql") {
			continue
		}
		files = append(files, e.Name())
	}
	sort.Strings(files)
	return files, nil
}

// Apply runs every not-yet-applied migration inside a transaction and
// records it in schema_migrations(name). Returns the names it applied.
func Apply(ctx context.Context, ex Executor, dir string) ([]string, error) {
	files, err := Discover(dir)
	if err != nil {
		return nil, err
	}

	if err := ex.Exec(ctx, `CREATE TABLE IF NOT EXISTS schema_migrations (
		name TEXT PRIMARY KEY,
		applied_at TIMESTAMPTZ NOT NULL DEFAULT now()
	)`); err != nil {
		return nil, fmt.Errorf("ensure schema_migrations: %w", err)
	}

	var applied []string
	for _, f := range files {
		_, found, err := ex.QueryString(ctx, "SELECT name FROM schema_migrations WHERE name = '"+f+"'")
		if err != nil {
			return applied, fmt.Errorf("check %s: %w", f, err)
		}
		if found {
			continue
		}
		body, err := os.ReadFile(filepath.Join(dir, f))
		if err != nil {
			return applied, fmt.Errorf("read %s: %w", f, err)
		}
		if err := ex.Exec(ctx, "BEGIN"); err != nil {
			return applied, fmt.Errorf("begin %s: %w", f, err)
		}
		if err := ex.Exec(ctx, string(body)); err != nil {
			_ = ex.Exec(ctx, "ROLLBACK")
			return applied, fmt.Errorf("apply %s: %w", f, err)
		}
		if err := ex.Exec(ctx, "INSERT INTO schema_migrations(name) VALUES ('"+f+"')"); err != nil {
			_ = ex.Exec(ctx, "ROLLBACK")
			return applied, fmt.Errorf("record %s: %w", f, err)
		}
		if err := ex.Exec(ctx, "COMMIT"); err != nil {
			return applied, fmt.Errorf("commit %s: %w", f, err)
		}
		applied = append(applied, f)
	}
	return applied, nil
}
