package migrate

import (
	"context"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

// fakeExec records executed statements and simulates schema_migrations.
type fakeExec struct {
	statements []string
	applied    map[string]bool
	failOn     string // Exec fails when the SQL contains this substring
}

func (f *fakeExec) Exec(_ context.Context, sql string) error {
	if f.failOn != "" && strings.Contains(sql, f.failOn) {
		return errSimulated
	}
	f.statements = append(f.statements, sql)
	if name, ok := insertedName(sql); ok {
		f.applied[name] = true
	}
	return nil
}

func (f *fakeExec) QueryString(_ context.Context, sql string) (string, bool, error) {
	name := selectedName(sql)
	return name, f.applied[name], nil
}

var errSimulated = &simulatedError{}

type simulatedError struct{}

func (*simulatedError) Error() string { return "simulated failure" }

// insertedName extracts the migration name from
// INSERT INTO schema_migrations(name) VALUES ('x.sql').
func insertedName(sql string) (string, bool) {
	const marker = "VALUES ('"
	i := strings.Index(sql, marker)
	if i < 0 {
		return "", false
	}
	rest := sql[i+len(marker):]
	if j := strings.Index(rest, "')"); j >= 0 {
		return rest[:j], true
	}
	return rest, true
}

// selectedName extracts the migration name from
// SELECT name FROM schema_migrations WHERE name = 'x.sql'.
func selectedName(sql string) string {
	const marker = "= '"
	i := strings.Index(sql, marker)
	if i < 0 {
		return ""
	}
	rest := sql[i+len(marker):]
	if j := strings.Index(rest, "'"); j >= 0 {
		return rest[:j]
	}
	return rest
}

func writeMigrations(t *testing.T, files map[string]string) string {
	t.Helper()
	dir := t.TempDir()
	for name, body := range files {
		if err := os.WriteFile(filepath.Join(dir, name), []byte(body), 0o644); err != nil {
			t.Fatal(err)
		}
	}
	return dir
}

func TestDiscoverOrdersAndFilters(t *testing.T) {
	dir := writeMigrations(t, map[string]string{
		"0002_second.sql": "SELECT 2;",
		"0001_first.sql":  "SELECT 1;",
		"notes.txt":       "ignore me",
		"0003_third.sql":  "SELECT 3;",
	})
	got, err := Discover(dir)
	if err != nil {
		t.Fatal(err)
	}
	want := []string{"0001_first.sql", "0002_second.sql", "0003_third.sql"}
	if len(got) != len(want) {
		t.Fatalf("Discover() = %v, want %v", got, want)
	}
	for i := range want {
		if got[i] != want[i] {
			t.Fatalf("Discover()[%d] = %q, want %q", i, got[i], want[i])
		}
	}
}

func TestDiscoverMissingDir(t *testing.T) {
	if _, err := Discover(filepath.Join(t.TempDir(), "nope")); err == nil {
		t.Fatal("expected error for missing dir")
	}
}

func TestApplyRunsNewMigrationsOnly(t *testing.T) {
	dir := writeMigrations(t, map[string]string{
		"0001_a.sql": "CREATE TABLE a();",
		"0002_b.sql": "CREATE TABLE b();",
	})
	fe := &fakeExec{applied: map[string]bool{}}

	first, err := Apply(context.Background(), fe, dir)
	if err != nil {
		t.Fatal(err)
	}
	if len(first) != 2 {
		t.Fatalf("first Apply applied %v, want 2 files", first)
	}

	second, err := Apply(context.Background(), fe, dir)
	if err != nil {
		t.Fatal(err)
	}
	if len(second) != 0 {
		t.Fatalf("second Apply applied %v, want none (idempotent)", second)
	}
}

func TestApplySkipsAlreadyAppliedAndStopsOnFailure(t *testing.T) {
	dir := writeMigrations(t, map[string]string{
		"0001_ok.sql": "CREATE TABLE ok();",
		"0002_bad.sql": "CREATE TABLE bad(",
	})
	fe := &fakeExec{
		applied: map[string]bool{"0001_ok.sql": true},
		failOn:  "CREATE TABLE bad",
	}

	applied, err := Apply(context.Background(), fe, dir)
	if err == nil {
		t.Fatal("expected failure on bad migration")
	}
	if len(applied) != 0 {
		t.Fatalf("applied %v, want none — 0001 already applied, 0002 must fail", applied)
	}
}
